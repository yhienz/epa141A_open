# Import general python packages
import pandas as pd
import copy

# Import functions
from dike_model_function import DikeNetwork  # @UnresolvedImport
from problem_formulation import get_model_for_problem_formulation
from problem_formulation import (sum_over, time_step_0,time_step_1,
                                 time_step_2, time_step_3, time_step_4)
# Loading in the necessary modules for EMA workbench and functions
from ema_workbench import (Model, MultiprocessingEvaluator, Scenario,
                           Constraint, ScalarOutcome)
from ema_workbench.util import ema_logging
from ema_workbench import save_results, load_results
from ema_workbench.em_framework.optimization import ArchiveLogger, EpsilonProgress
from ema_workbench.em_framework.optimization import epsilon_nondominated, to_problem

def initialize_model():
    ema_logging.log_to_stderr(ema_logging.INFO)
    print("Initializing model...")
    dike_model, planning_steps = get_model_for_problem_formulation(7)
    print("Model initialized.")
    return dike_model, planning_steps

# Writing a function to create actor specific problem formulations
def problem_formulation_actor(problem_formulation_actor, uncertainties, levers):
    # Load the model:
    function = DikeNetwork()
    # workbench model:
    model = Model('dikesnet', function=function)
    # Outcomes are all costs, thus they have to minimized:
    direction = ScalarOutcome.MINIMIZE

    model.uncertainties = uncertainties
    model.levers = levers

    cost_variables = []
    cost_variables.extend(
    [
        f"{dike}_{e}"
        for e in ["Expected Annual Damage", "Dike Investment Costs"]
        for dike in function.dikelist
    ])
    cost_variables.extend([f"RfR Total Costs"])
    cost_variables.extend([f"Expected Evacuation Costs"])

    if problem_formulation_actor == 6:  # GELDERLAND
        model.outcomes.clear()
        model.outcomes = [
            ScalarOutcome(f'Total_period_Costs_0',
                          variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
                          function=time_step_0, kind=direction),
            ScalarOutcome(f'Total_period_Costs_1',
                          variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
                          function=time_step_1, kind=direction),
            ScalarOutcome(f'Total_period_Costs_2',
                          variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
                          function=time_step_2, kind=direction),
            # ScalarOutcome(f'Total_period_Costs_3',
            #               variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
            #               function=time_step_3, kind=direction),
            # ScalarOutcome(f'Total_period_Costs_4',
            #               variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
            #               function=time_step_4, kind=direction),
            ScalarOutcome('Expected Annual Damage A1_', variable_name='A.1_Expected Annual Damage', function=sum_over,
                          kind=direction),
            ScalarOutcome('Expected Annual Damage A2_', variable_name='A.2_Expected Annual Damage', function=sum_over,
                          kind=direction),
            ScalarOutcome('Expected Annual Damage A3_', variable_name='A.3_Expected Annual Damage', function=sum_over,
                          kind=direction),
            ScalarOutcome('Total Costs', variable_name=cost_variables, function=sum_over, kind=direction),
            ScalarOutcome("Expected Number of Deaths_", variable_name=
            [f"{dike}_Expected Number of Deaths" for dike in function.dikelist], function=sum_over, kind=direction)]


    elif problem_formulation_actor == 7:  # OVERIJSSEL
        model.outcomes.clear()
        model.outcomes = [
            ScalarOutcome(f'Total_period_Costs_0',
                          variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
                          function=time_step_0, kind=direction),
            ScalarOutcome(f'Total_period_Costs_1',
                          variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
                          function=time_step_1, kind=direction),
            ScalarOutcome(f'Total_period_Costs_2',
                          variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
                          function=time_step_2, kind=direction),
            # ScalarOutcome(f'Total_period_Costs_3',
            #               variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
            #               function=time_step_3, kind=direction),
            # # ScalarOutcome(f'Total_period_Costs_4',
            #               variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
            #               function=time_step_4, kind=direction),
            ScalarOutcome('Expected Annual Damage A4_', variable_name='A.4_Expected Annual Damage', function=sum_over,
                          kind=direction),
            ScalarOutcome('Expected Annual Damage A5_', variable_name='A.5_Expected Annual Damage', function=sum_over,
                          kind=direction),
            ScalarOutcome('Total Costs', variable_name=cost_variables, function=sum_over, kind=direction),
            ScalarOutcome("Expected Number of Deaths_", variable_name=
            [f"{dike}_Expected Number of Deaths" for dike in function.dikelist], function=sum_over, kind=direction)]

    else:
        raise TypeError('unknown identifier')
    return model

### Overijssel
if __name__ == '__main__':
    dike_model, planning_steps = initialize_model()

    uncertainties = dike_model.uncertainties
    levers = dike_model.levers

    # Setting the reference scenario
    reference_values = {
        "Bmax": 175,
        "Brate": 1.5,
        "pfail": 0.5,
        "ID flood wave shape": 4,
        "planning steps": 2,
    }
    reference_values.update({f"discount rate {n}": 3.5 for n in planning_steps})
    refcase_scen = {}

    for key in dike_model.uncertainties:
        name_split = key.name.split('_')
        if len(name_split) == 1:
            refcase_scen.update({key.name: reference_values[key.name]})
        else:
            refcase_scen.update({key.name: reference_values[name_split[1]]})

    ref_scenario = Scenario('reference', **refcase_scen)

    ######### Overijssel
    model = problem_formulation_actor(6, uncertainties, levers)

    # Deepcopying the uncertainties and levers
    uncertainties = copy.deepcopy(dike_model.uncertainties)
    levers = copy.deepcopy(dike_model.levers)

    # Running the optimization for Overijssel
    function = DikeNetwork()
    convergence_metrics = {EpsilonProgress()}
    #constraint = [Constraint("Total period Costs", outcome_names= [f"{dike}_Expected Number of Deaths" for dike in function.dikelist], function=lambda x: max(0, x - 100000000))]

    results_epsilon = pd.DataFrame()  # Initialize an empty DataFrame
    results_outcomes = pd.DataFrame()
    results=[]
    with MultiprocessingEvaluator(model) as evaluator:
        for _ in range(3):
            #
            # convergence_metrics = [
            #     ArchiveLogger(
            #         "./archives",
            #         [l.name for l in model.levers],
            #         [o.name for o in model.outcomes],
            #         base_filename=f"{_}.tar.gz",
            #     ),
            #     EpsilonProgress(),
            # ]


            result = evaluator.optimize(nfe=25000, searchover='levers',
                                        convergence=convergence_metrics,
                                        epsilons=[0.01] * len(model.outcomes), reference=ref_scenario)
            y,t = result
            results.append(result)
            results_epsilon = pd.concat([results_epsilon, t])
            results_outcomes = pd.concat([results_outcomes, y])

    # all_archives = []
    #
    # for i in range(2):
    #     archives = ArchiveLogger.load_archives(f"./archives/{i}.tar.gz")
    #     all_archives.append(archives)

    # print(reference_set.shape)
    # print(type(reference_set))
    # print(reference_set.head())

    # Save the concatenated DataFrame to a CSV file
    results_epsilon.to_csv('Week25_MORDM_epsilon_Gelderland_PD7_.csv', index=False)
    results_outcomes.to_csv('Week25_MORDM_outcomes_Gelderland_PD7_.csv', index=False)

    ### Gelderland Exploration

    policy_set = results_outcomes.loc[~results_outcomes.iloc[:, 1:51].duplicated()]
    policies = policy_set.iloc[:,1:51]

    from ema_workbench import Policy

    rcase_policies = []

    for i, policy in policies.iterrows():
        rcase_policies.append(Policy(str(i), **policy.to_dict()))

    n_scenarios = 2000
    with MultiprocessingEvaluator(model) as evaluator:
        reference_policies_results = evaluator.perform_experiments(n_scenarios,
                                                rcase_policies)
    save_results(reference_policies_results, 'Week25_Gelderland.tar.gz')
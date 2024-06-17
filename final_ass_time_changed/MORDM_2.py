# Import general python packages
import pandas as pd
import copy

# Import functions
from dike_model_function import DikeNetwork  # @UnresolvedImport
from problem_formulation import get_model_for_problem_formulation
from problem_formulation import sum_over, stick_over_time, slick_over_time, sick_over_time, lick_over_time, kick_over_time

# Loading in the necessary modules for EMA workbench and functions
from ema_workbench import (Model, MultiprocessingEvaluator, Scenario,
                           Constraint, ScalarOutcome)
from ema_workbench.util import ema_logging
from ema_workbench import save_results, load_results
from ema_workbench.em_framework.optimization import (EpsilonProgress)

def initialize_model():
    ema_logging.log_to_stderr(ema_logging.INFO)
    print("Initializing model...")
    dike_model, planning_steps = get_model_for_problem_formulation(6)
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

    if problem_formulation_actor == 5:  # GELDERLAND
        model.outcomes.clear()
        model.outcomes = [
            ScalarOutcome(f'Total_period_Costs_0',
                          variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
                          function=stick_over_time, kind=direction),
            ScalarOutcome(f'Total_period_Costs_1',
                          variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
                          function=slick_over_time, kind=direction),
            ScalarOutcome(f'Total_period_Costs_2',
                          variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
                          function=sick_over_time, kind=direction),
            ScalarOutcome(f'Total_period_Costs_3',
                          variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
                          function=lick_over_time, kind=direction),
            ScalarOutcome(f'Total_period_Costs_4',
                          variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
                          function=kick_over_time, kind=direction),
            ScalarOutcome('Expected Annual Damage A1', variable_name='A.1_Expected Annual Damage', function=sum_over,
                          kind=direction),
            ScalarOutcome('Expected Annual Damage A2', variable_name='A.2_Expected Annual Damage', function=sum_over,
                          kind=direction),
            ScalarOutcome('Expected Annual Damage A3', variable_name='A.3_Expected Annual Damage', function=sum_over,
                          kind=direction),
            ScalarOutcome("Expected Number of Deaths", variable_name=
            [f"{dike}_Expected Number of Deaths" for dike in function.dikelist], function=sum_over, kind=direction)]


    elif problem_formulation_actor == 6:  # OVERIJSSEL
        model.outcomes.clear()
        model.outcomes = [
            ScalarOutcome(f'Total_period_Costs_0',
                          variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
                          function=stick_over_time, kind=direction),
            ScalarOutcome(f'Total_period_Costs_1',
                          variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
                          function=slick_over_time, kind=direction),
            ScalarOutcome(f'Total_period_Costs_2',
                          variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
                          function=sick_over_time, kind=direction),
            ScalarOutcome(f'Total_period_Costs_3',
                          variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
                          function=lick_over_time, kind=direction),
            ScalarOutcome(f'Total_period_Costs_4',
                          variable_name=dike_model.outcomes['Total_period_Costs'].variable_name,
                          function=kick_over_time, kind=direction),
            ScalarOutcome('Expected Annual Damage A4', variable_name='A.4_Expected Annual Damage', function=sum_over,
                          kind=direction),
            ScalarOutcome('Expected Annual Damage A5', variable_name='A.5_Expected Annual Damage', function=sum_over,
                          kind=direction),
            ScalarOutcome("Expected Number of Deaths", variable_name=
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
    constraint = [Constraint("Total period Costs", outcome_names= [f"{dike}_Expected Number of Deaths" for dike in function.dikelist], function=lambda x: max(0, x - 100000000))]

    results_epsilon = pd.DataFrame()  # Initialize an empty DataFrame
    results_outcomes = pd.DataFrame()
    with MultiprocessingEvaluator(model) as evaluator:
        for _ in range(3):
            (y, t) = evaluator.optimize(nfe=25000, searchover='levers',
                                        convergence=convergence_metrics,
                                        epsilons=[0.1] * len(model.outcomes), reference=ref_scenario,
                                        constraints=constraint)

            results_epsilon = pd.concat([results_epsilon, t])
            results_outcomes = pd.concat([results_outcomes, y])



    # Save the concatenated DataFrame to a CSV file
    results_epsilon.to_csv('Week24_MORDM_epsilon_overijssel_PD7.csv', index=False)
    results_outcomes.to_csv('Week24_MORDM_outcomes_overijssel_PD7.csv', index=False)


# ######### Gelderland
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
    model2 = problem_formulation_actor(5, uncertainties, levers)

    constraint = [Constraint("Total period Costs",
                             outcome_names=[f"{dike}_Expected Number of Deaths" for dike in function.dikelist],
                             function=lambda x: max(0, x - 100000000))]

    results_epsilon2 = pd.DataFrame()  # Initialize an empty DataFrame
    results_outcomes2 = pd.DataFrame()
    with MultiprocessingEvaluator(model2) as evaluator:
        for _ in range(3):
            (y, t) = evaluator.optimize(nfe=25000, searchover='levers',
                                        convergence=convergence_metrics,
                                        epsilons=[0.1] * len(model2.outcomes), reference=ref_scenario,
                                        constraints=constraint)

            results_epsilon2 = pd.concat([results_epsilon2, t])
            results_outcomes2 = pd.concat([results_outcomes2, y])


    # Save the concatenated DataFrame to a CSV file
    results_epsilon2.to_csv('Week23_MORDM_Gelderland_PD7.csv', index=False)
    results_outcomes2.to_csv('Week23_MORDM_Gelderland_PD7.csv', index=False)

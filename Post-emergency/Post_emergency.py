

#This version finds a solution to the post-emergency problem by solving a satisfaction problem with a given maximum time limit for acceptable solutions.
#Patients are simply assigned to operators (exactly one operator per patient). The operator's time is updated by adding patients' processing times until all patients have been processed. When all the patients have been processed, the assignment is complete (the operator times are definitive), but only if the operator's time is not greater than the given time limit, its plan can be submitted. If all operators can submit a plan, an admissible solution has been found to the problem.


from unified_planning.shortcuts import *
from unified_planning.engines import PlanGenerationResultStatus

up.shortcuts.get_env().credits_stream = None

def readInput(path_to_input_file):
    f = open(path_to_input_file,"r")
    lines = f.readlines()
    f.close()
    patients_info = lines[0].strip().split(" ")
    operators_info = lines[1].strip().split(" ")
    number_of_patients = int(patients_info[0])
    number_of_operators = int(operators_info[0])
    patient_costs = patients_info[1:number_of_patients + 1]
    operators_costs = operators_info[1:number_of_operators + 1]

    return [number_of_patients, number_of_operators, patient_costs, operators_costs]



PATH_TO_INPUT = sys.argv[1]
VERBOSE = sys.argv[2] != '0'
PATH_TO_OUTPUT = sys.argv[3]
TIME_LIMIT = int(sys.argv[4])

[NUMBER_OF_PATIENTS, NUMBER_OF_OPERATORS, PATIENT_COSTS, OPERATOR_COSTS] = readInput(PATH_TO_INPUT)

Patient = UserType('Patient')
Operator = UserType('Operator')

patients = [Object('p%s' % i, Patient) for i in range(NUMBER_OF_PATIENTS)]
operators = [Object('o%s' % i, Operator) for i in range(NUMBER_OF_OPERATORS)]

p_var = Variable("p_var", Patient)
o_var = Variable("o_var", Operator)

processed = Fluent("processed", BoolType(), p=Patient)
processing_time = Fluent('processing_time', IntType(0), p=Patient)
operator_time = Fluent('operator_time', IntType(0), o=Operator)
submitted_plan = Fluent("submitted_plan", BoolType(), o=Operator)
maximum_operator_time = Fluent("maximum_operator_time", IntType(0))

assign_patient = InstantaneousAction("assign_patient", p=Patient, o=Operator)
p = assign_patient.parameter('p')
o = assign_patient.parameter('o')
assign_patient.add_precondition(Not(processed(p)))
#assign_patient.add_precondition(LE(operator_time(o), maximum_operator_time()))
assign_patient.add_increase_effect(operator_time(o), processing_time(p))
assign_patient.add_effect(processed(p), True)

submit_operator_plan = InstantaneousAction("submit_operator_plan", o=Operator)
o = submit_operator_plan.parameter('o')
submit_operator_plan.add_precondition(Forall(processed(p_var), p_var))
submit_operator_plan.add_precondition(Not(submitted_plan(o)))
submit_operator_plan.add_precondition(LE(operator_time(o), maximum_operator_time()))
submit_operator_plan.add_effect(submitted_plan(o), True)

problem = Problem('post-emergency')
problem.add_objects(patients)
problem.add_objects(operators)
problem.add_fluent(processed, default_initial_value=False)
problem.add_fluent(processing_time, default_initial_value=0)
problem.add_fluent(operator_time, default_initial_value=0)
problem.add_fluent(submitted_plan, default_initial_value=False)
problem.add_fluent(maximum_operator_time, default_initial_value=0)
problem.add_action(assign_patient)
problem.add_action(submit_operator_plan)
problem.add_goal(Forall(submitted_plan(o_var), o_var))

for p in range(NUMBER_OF_PATIENTS):
    problem.set_initial_value(processing_time(patients[p]), int(PATIENT_COSTS[p]))
for o in range(NUMBER_OF_OPERATORS):
    problem.set_initial_value(operator_time(operators[o]), int(OPERATOR_COSTS[o]))
problem.set_initial_value(maximum_operator_time(), TIME_LIMIT)

print("Attempting to solve problem with a time limit of " + str(TIME_LIMIT))

if(VERBOSE):
    print(problem)

with OneshotPlanner(name='enhsp-opt') as planner:
    result = planner.solve(problem)
    if(VERBOSE):
        for m in range(len(result.log_messages)):
            print(result.log_messages[m].level)
            print(result.log_messages[m].message)
            print()
        print(result.status)


if result.status == PlanGenerationResultStatus.UNSOLVABLE_PROVEN:
    print("Problem is unsolvable with a time limit of " + str(TIME_LIMIT))
    sys.exit(-1)
elif result.status == PlanGenerationResultStatus.SOLVED_OPTIMALLY or result.status == PlanGenerationResultStatus.SOLVED_SATISFICING:
    print("Problem solved within the time limit of " + str(TIME_LIMIT))
    print(result.plan)
    f = open(PATH_TO_OUTPUT,"w")
    print(result.plan,file=f)
    f.close()
    sys.exit(0)
else:
    print("Problem lead to an internal error.")
    sys.exit(1)

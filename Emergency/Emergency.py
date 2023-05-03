#Alternative, equivalent formulation to emercency problem

#@note Calculating the total distance as a simple maximum among operator's distances seems to not work; instead, it is necessary to assign weights to the edges of linear graph (proportional to r^n) and compute the total distance as a sum.
#@note Using conditional effects seems not allowed: it is not clear how to update the count of selected operators for every role when a new operator is selected. For handling this, a second move has been introduced in order to set the roles for the selected operators.
#@note The expression "with OneshotPlanner(problem_kind=problem.kind, optimality_guarantee=PlanGenerationResultStatus.SOLVED_OPTIMALLY) as planner:" does not select any planner because the add_increase_effect function takes as arguments quantities that may not be constant. In practise, however, these quantities are never changed and forcing the execution with "with OneshotPlanner(name='enhsp-opt') as planner:" should lead to correct results.


from asyncio.windows_events import INFINITE
import unified_planning
from unified_planning.shortcuts import *
from unified_planning.engines import PlanGenerationResultStatus


#functions
def computeDistance(roomIndex):
    if roomIndex == 0:
        return 0
    return (int)((1 - pow(NUMBER_OF_ROLES, roomIndex))/(1-NUMBER_OF_ROLES))


#input
input_filename = sys.argv[1]
f = open(input_filename,"r")
lines = f.readlines()
cardinalities = lines[0].split(" ")
NUMBER_OF_LOCATIONS = int(cardinalities[0])
NUMBER_OF_OPERATORS = int(cardinalities[1])
NUMBER_OF_ROLES = int(cardinalities[2])
f.close()


#types
Operator = UserType('Operator')
Role = UserType('Role')


#objects
operators = [Object('o%s' % i, Operator) for i in range(NUMBER_OF_OPERATORS)]
roles = [Object('r%s' % i, Role) for i in range(NUMBER_OF_ROLES)]


#fluents
is_selected = Fluent('is_selected', BoolType(), o=Operator)
has_role = Fluent('has_role', BoolType(), o=Operator, r=Role)
operator_distance = Fluent('operator_distance', IntType(0, INFINITE), o=Operator)
number_of_selected_operators = Fluent('number_of_selected_operators', IntType(0, NUMBER_OF_OPERATORS + 1), r=Role)
max_distance = Fluent('max_distance', IntType(0, INFINITE))


#actions
move = InstantaneousAction('select', o=Operator)
o = move.parameter('o')
move.add_precondition(Not(is_selected(o)))
move.add_effect(is_selected(o), True)
#move.add_effect(max_distance(), operator_distance(o), GT(operator_distance(o), max_distance()))
move.add_increase_effect(max_distance(), operator_distance(o))
#for r in range(NUMBER_OF_ROLES):
#    move.add_increase_effect(number_of_selected_operators(roles[r]), 1, problem.initial_value(has_role(o, roles[r])).constant_value())#@todo Here is the problem: how to define conditional effect

set_role = InstantaneousAction('set_role', o=Operator, r=Role)
o = set_role.parameter('o')
r = set_role.parameter('r')
set_role.add_precondition(is_selected(o))
set_role.add_precondition(has_role(o, r))
set_role.add_increase_effect(number_of_selected_operators(r), 1)
set_role.add_effect(has_role(o, r), False)

#problem
problem = Problem('emergency')
problem.add_objects(operators)
problem.add_objects(roles)
problem.add_fluent(is_selected, default_initial_value=False)
problem.add_fluent(has_role, default_initial_value=False)
problem.add_fluent(operator_distance, default_initial_value=0)
problem.add_fluent(number_of_selected_operators, default_initial_value=0)
problem.add_fluent(max_distance, default_initial_value=0)
problem.add_action(move)
problem.add_action(set_role)

#initializations
for o in range (NUMBER_OF_OPERATORS):
    operator_values = lines[o+1].split(" ")
    operator_room = operator_values[0]
    problem.set_initial_value(operator_distance(operators[o]), computeDistance(int(operator_room)))
    #problem.set_initial_value(operator_distance(operators[o]), int(operator_room))
    for i in range (len(operator_values) - 1):
        problem.set_initial_value(has_role(operators[o], roles[int(operator_values[i+1])]), True)


for o in range(NUMBER_OF_OPERATORS):
    if problem.initial_value(operator_distance(operators[o])).constant_value() == 0:
        problem.set_initial_value(is_selected(operators[o]), True)


#goals
required_roles_cardinality = lines[NUMBER_OF_OPERATORS+1].split(" ")
for r in range (len(required_roles_cardinality)):
    required_number_of_operators_for_role = int(required_roles_cardinality[r])
    if required_number_of_operators_for_role>0:
        problem.add_goal(Equals(number_of_selected_operators(roles[r]), required_number_of_operators_for_role))


#metrics
problem.add_quality_metric(up.model.metrics.MinimizeExpressionOnFinalState(max_distance()))
#problem.add_quality_metric(up.model.metrics.MinimizeSequentialPlanLength())


#solution
print(problem)
with OneshotPlanner(name='enhsp-opt') as planner:
#with OneshotPlanner(problem_kind=problem.kind, optimality_guarantee=PlanGenerationResultStatus.SOLVED_OPTIMALLY) as planner:
    result = planner.solve(problem)
    for m in range(len(result.log_messages)):
        print(result.log_messages[m].level)
        print(result.log_messages[m].message)
        print()
    print(result.status)

if len(sys.argv)==3 :
    output_filename = sys.argv[2]
    f = open(output_filename,"w")
    print(result.plan,file=f)
    f.close()
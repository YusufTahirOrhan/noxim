#include "Selection_DEFT_QL.h"

#include "../DeftLateBinding.h"

SelectionStrategiesRegister Selection_DEFT_QL::selectionStrategiesRegister("DEFT_QL", getInstance());

Selection_DEFT_QL * Selection_DEFT_QL::instance = 0;

Selection_DEFT_QL * Selection_DEFT_QL::getInstance() {
	if ( instance == 0 )
		instance = new Selection_DEFT_QL();
	return instance;
}

int Selection_DEFT_QL::apply(Router * router, const vector < int >&directions, const RouteData & route_data){
    assert(directions.size()!=0);
    return DeftLB::selectQLearning(router, directions, route_data);
}

void Selection_DEFT_QL::perCycleUpdate(Router * router){ (void) router; }

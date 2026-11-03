#include "Selection_DEFT_FAST.h"

#include "../DeftLateBinding.h"

SelectionStrategiesRegister Selection_DEFT_FAST::selectionStrategiesRegister("DEFT_FAST", getInstance());

Selection_DEFT_FAST * Selection_DEFT_FAST::instance = 0;

Selection_DEFT_FAST * Selection_DEFT_FAST::getInstance() {
	if ( instance == 0 )
		instance = new Selection_DEFT_FAST();
	return instance;
}

int Selection_DEFT_FAST::apply(Router * router, const vector < int >&directions, const RouteData & route_data){
    assert(directions.size()!=0);
    return DeftLB::selectFast(router, directions, route_data);
}

void Selection_DEFT_FAST::perCycleUpdate(Router * router){ (void) router; }

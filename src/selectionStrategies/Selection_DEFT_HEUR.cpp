#include "Selection_DEFT_HEUR.h"

#include "../DeftLateBinding.h"

SelectionStrategiesRegister Selection_DEFT_HEUR::selectionStrategiesRegister("DEFT_HEUR", getInstance());

Selection_DEFT_HEUR * Selection_DEFT_HEUR::instance = 0;

Selection_DEFT_HEUR * Selection_DEFT_HEUR::getInstance() {
	if ( instance == 0 )
		instance = new Selection_DEFT_HEUR();
	return instance;
}

int Selection_DEFT_HEUR::apply(Router * router, const vector < int >&directions, const RouteData & route_data){
    assert(directions.size()!=0);
    return DeftLB::selectHeuristic(router, directions, route_data);
}

void Selection_DEFT_HEUR::perCycleUpdate(Router * router){ (void) router; }

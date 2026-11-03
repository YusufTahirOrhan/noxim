#ifndef __NOXIMSELECTION_DEFT_FAST_H__
#define __NOXIMSELECTION_DEFT_FAST_H__

#include "SelectionStrategy.h"
#include "SelectionStrategies.h"
#include "../Router.h"

using namespace std;

class Selection_DEFT_FAST : SelectionStrategy {
	public:
        int apply(Router * router, const vector < int >&directions, const RouteData & route_data);
        void perCycleUpdate(Router * router);

		static Selection_DEFT_FAST * getInstance();

	private:
		Selection_DEFT_FAST(){};
		~Selection_DEFT_FAST(){};

		static Selection_DEFT_FAST * instance;
		static SelectionStrategiesRegister selectionStrategiesRegister;
};

#endif

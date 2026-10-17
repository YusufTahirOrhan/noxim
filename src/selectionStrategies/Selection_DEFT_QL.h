#ifndef __NOXIMSELECTION_DEFT_QL_H__
#define __NOXIMSELECTION_DEFT_QL_H__

#include "SelectionStrategy.h"
#include "SelectionStrategies.h"
#include "../Router.h"

using namespace std;

class Selection_DEFT_QL : SelectionStrategy {
	public:
        int apply(Router * router, const vector < int >&directions, const RouteData & route_data);
        void perCycleUpdate(Router * router);

		static Selection_DEFT_QL * getInstance();

	private:
		Selection_DEFT_QL(){};
		~Selection_DEFT_QL(){};

		static Selection_DEFT_QL * instance;
		static SelectionStrategiesRegister selectionStrategiesRegister;
};

#endif

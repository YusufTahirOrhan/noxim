#ifndef __NOXIMSELECTION_DEFT_HEUR_H__
#define __NOXIMSELECTION_DEFT_HEUR_H__

#include "SelectionStrategy.h"
#include "SelectionStrategies.h"
#include "../Router.h"

using namespace std;

class Selection_DEFT_HEUR : SelectionStrategy {
	public:
        int apply(Router * router, const vector < int >&directions, const RouteData & route_data);
        void perCycleUpdate(Router * router);

		static Selection_DEFT_HEUR * getInstance();

	private:
		Selection_DEFT_HEUR(){};
		~Selection_DEFT_HEUR(){};

		static Selection_DEFT_HEUR * instance;
		static SelectionStrategiesRegister selectionStrategiesRegister;
};

#endif

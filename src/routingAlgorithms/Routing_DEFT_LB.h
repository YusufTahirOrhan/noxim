#ifndef __NOXIMROUTING_DEFT_LB_H__
#define __NOXIMROUTING_DEFT_LB_H__

#include "RoutingAlgorithm.h"
#include "RoutingAlgorithms.h"
#include "../Router.h"

using namespace std;

// Late-binding DeFT routing relation (see DeftLateBinding.h).
class Routing_DEFT_LB : RoutingAlgorithm {
    public:
        vector<int> route(Router * router, const RouteData & routeData);

        static Routing_DEFT_LB * getInstance();

    private:
        Routing_DEFT_LB(){};
        ~Routing_DEFT_LB(){};

        static Routing_DEFT_LB * routing_DEFT_LB;
        static RoutingAlgorithmsRegister routingAlgorithmsRegister;
};

#endif

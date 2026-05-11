#ifndef __NOXIMROUTING_INTERPOSER_AWARE_XY_H__
#define __NOXIMROUTING_INTERPOSER_AWARE_XY_H__

#include "RoutingAlgorithm.h"
#include "RoutingAlgorithms.h"
#include "../Router.h"

using namespace std;

class Routing_INTERPOSER_AWARE_XY : RoutingAlgorithm {
    public:
        vector<int> route(Router * router, const RouteData & routeData);

        static Routing_INTERPOSER_AWARE_XY * getInstance();

    private:
        Routing_INTERPOSER_AWARE_XY(){};
        ~Routing_INTERPOSER_AWARE_XY(){};

        static Routing_INTERPOSER_AWARE_XY * routing_INTERPOSER_AWARE_XY;
        static RoutingAlgorithmsRegister routingAlgorithmsRegister;
};

#endif

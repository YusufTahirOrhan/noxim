#include "Routing_DEFT_LB.h"

#include "../DeftLateBinding.h"

RoutingAlgorithmsRegister Routing_DEFT_LB::routingAlgorithmsRegister("DEFT_LB", getInstance());

Routing_DEFT_LB * Routing_DEFT_LB::routing_DEFT_LB = 0;

Routing_DEFT_LB * Routing_DEFT_LB::getInstance() {
    if ( routing_DEFT_LB == 0 )
        routing_DEFT_LB = new Routing_DEFT_LB();

    return routing_DEFT_LB;
}

vector<int> Routing_DEFT_LB::route(Router * router, const RouteData & routeData)
{
    (void) router;
    vector<int> directions;
    DeftLB::legalMoves(routeData, &directions);
    return directions;
}

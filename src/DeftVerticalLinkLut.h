/*
 * DeFT runtime Vertical Link lookup table loader.
 */

#ifndef __NOXIMDEFTVERTICALLINKLUT_H__
#define __NOXIMDEFTVERTICALLINKLUT_H__

#include <cstddef>
#include <stdint.h>
#include <string>
#include <vector>

namespace DeftVerticalLinkLut {

struct VerticalLinkSelection {
    VerticalLinkSelection();

    int selected_vl_id;
    int boundary_router_id;
    int interposer_endpoint_router_id;
    std::vector<int> ranked_vl_ids;
};

struct Entry {
    Entry();

    uint64_t fault_mask;
    int source_chiplet_id;
    int source_router_id;
    int destination_chiplet_id;
    VerticalLinkSelection source_exit;
    VerticalLinkSelection destination_entry;
};

bool loadFromFile(const std::string &filename,
                  std::string *error_message = 0);
bool isLoaded();
std::string loadedFilename();
std::size_t entryCount();
std::size_t activeFaultMaskEntryCount();
uint64_t currentFaultMask();
std::string currentFaultMaskId();
// "0x" followed by ceil(VerticalLinkCount / 4) hex digits (0x0000 for 16 VLs)
std::string formatFaultMask(uint64_t fault_mask);

bool lookup(int source_chiplet_id,
            int source_router_id,
            int destination_chiplet_id,
            Entry *entry,
            std::string *error_message = 0);

} // namespace DeftVerticalLinkLut

#endif

#include <cstdlib>
#include <iostream>
#include <vector>
#include <map>
#include <string>
#include <boost/assign.hpp>

int main()
{
    std::vector<int> v = boost::assign::list_of(1)(2)(3);
    std::map<int, std::string> m = boost::assign::map_list_of(1, "a")(2, "b")(3, "c");
    
    std::cout << "v: ";
    for (std::vector<int>::const_iterator i = v.begin(); i != v.end(); ++i)
        std::cout << *i << " ";
    std::cout << std::endl;
    std::cout << "m: ";
    for (std::map<int, std::string>::const_iterator i = m.begin(); i != m.end(); ++i)
        std::cout << i->first << "," << i->second << " ";
    std::cout << std::endl;
    return EXIT_SUCCESS;
}

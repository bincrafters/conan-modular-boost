#include <iostream>
#include <vector>
#include <boost/algorithm/string.hpp>

int main()
{
    std::vector<std::string> list;
    list.push_back("Hello");
    list.push_back("World!");

    std::string joined = boost::algorithm::join(list, ", ");
    std::cout << joined << '\n';
}

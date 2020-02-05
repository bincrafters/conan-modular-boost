#include <iostream>
#include <string>
#include <boost/optional/optional.hpp>

int main()
{
    boost::optional<std::string> op("hello");

    std::cout << *op << '\n';
}

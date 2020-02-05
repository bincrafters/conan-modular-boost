#include <cstdlib>
#include <iostream>
#include <boost/array.hpp>

int main()
{
    typedef boost::array<int, 5> sample_array_t;
    sample_array_t a = {{ 1, 2, 3, 4, 5}};
    for (sample_array_t::const_iterator i = a.begin(); i != a.end(); ++i)
        std::cout << *i << " ";
    std::cout << std::endl;
    for (sample_array_t::const_reverse_iterator i = a.rbegin(); i != a.rend(); ++i)
        std::cout << *i << " ";
    return EXIT_SUCCESS;
}

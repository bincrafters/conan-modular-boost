#include <cstdlib>
#include <iostream>
#include <boost/rational.hpp>

int main()
{
    std::cout << "1/2 + 2/3 = " << (boost::rational<int>(1, 2) + boost::rational<int>(2, 3)) << std::endl;
    std::cout << "2/3 * 3/4 = " << (boost::rational<int>(2, 3) * boost::rational<int>(3, 4)) << std::endl;
    std::cout << "4/5 - 5/6 = " << (boost::rational<int>(4, 5) - boost::rational<int>(5, 6)) << std::endl;
    std::cout << "6/7 : 7/8 = " << (boost::rational<int>(6, 7) / boost::rational<int>(7, 8)) << std::endl;
    return EXIT_SUCCESS;
}

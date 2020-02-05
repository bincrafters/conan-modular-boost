#include <cstdlib>
#include <iostream>
#include <boost/bind.hpp>

static int sum_of_three(int a, int b, int c)
{
    return a + b + c;
}

int main()
{
    std::cout << "1 + 2 + 3 = " << boost::bind(sum_of_three, 1, 2, _1)(3) << std::endl;
    return EXIT_SUCCESS;
}

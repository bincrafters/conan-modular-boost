#include <cstdlib>
#include <iostream>
#include <boost/function.hpp>

int sum(int a, int b)
{
    return a + b;
}

struct sub
{
    int operator()(int a, int b) { return a - b; }
};

int main()
{
    boost::function<int(int, int)> f;
    f = sum;
    std::cout << "1 + 2 = " << f(1, 2) << std::endl;
    f = sub();
    std::cout << "2 - 1 = " << f(2, 1) << std::endl;
    return EXIT_SUCCESS;
}

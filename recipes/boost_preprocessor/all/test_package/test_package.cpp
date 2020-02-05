#include <iostream>
#include <boost/preprocessor/tuple/elem.hpp>

int main()
{
    int a = 0;

#define TUPLE3     (f(12), a + 1, foo)
                                  // length  index  tuple
    std::cout << BOOST_PP_TUPLE_ELEM(  3   ,  1  , TUPLE3)  << std::endl;
}

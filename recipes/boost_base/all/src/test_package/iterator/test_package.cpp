#include <cstdlib>
#include <iostream>
#include <vector>
#include <algorithm>
#include <numeric>
#include <functional>
#include <iterator>
#include <boost/iterator/filter_iterator.hpp>

struct is_odd
{
    bool operator()(int a) { return 0 != a % 2; }
};

struct is_even
{
    bool operator()(int a) { return 0 == a % 2; }
};

struct sequence
{
    sequence() : index(0) {}
    int operator()() { return index++; }
    int index;
};

int main()
{
    std::vector<int> v(10);
    std::generate(v.begin(), v.end(), sequence());
    std::cout << "odd numbers: ";
    std::copy(
        boost::make_filter_iterator<is_odd>(v.begin(), v.end()),
        boost::make_filter_iterator<is_odd>(v.end(), v.end()),
        std::ostream_iterator<int>(std::cout, " "));
    std::cout << std::endl;
    std::cout << "even numbers: ";
    std::copy(
        boost::make_filter_iterator<is_even>(v.begin(), v.end()),
        boost::make_filter_iterator<is_even>(v.end(), v.end()),
        std::ostream_iterator<int>(std::cout, " "));
    std::cout << std::endl;

    return EXIT_SUCCESS;
}

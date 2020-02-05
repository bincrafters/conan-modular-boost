#include <boost/serialization/detail/stack_constructor.hpp>

int main()
{
	boost::serialization::detail::stack_allocate<int>();
}


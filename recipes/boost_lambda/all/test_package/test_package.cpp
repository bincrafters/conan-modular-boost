#include <iostream>
#include <vector>
#include <boost/lambda/lambda.hpp>

int main()
{
	std::vector<int> v(3);
	for_each(v.begin(), v.end(), boost::lambda::_1 = 1);
	for (std::vector<int>::iterator i = v.begin(); i != v.end(); ++i)
		std::cout << *i << std::endl;
	return 0;
}

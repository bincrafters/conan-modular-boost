#include <boost/pool/pool.hpp>

int main()
{
	boost::pool<> p(sizeof(int));
}


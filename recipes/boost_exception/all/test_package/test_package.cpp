#include <boost/exception/all.hpp>

int main()
{
	typedef boost::error_info<struct tag_errmsg, std::string> errmsg_info;
}


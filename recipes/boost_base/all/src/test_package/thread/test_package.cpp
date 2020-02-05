#include <iostream>
#include <boost/thread/thread.hpp>

void my_func() 
{
  std::cout << "Hello, world!\n";
}

int main()
{
  boost::thread t(my_func);
  t.join();
}

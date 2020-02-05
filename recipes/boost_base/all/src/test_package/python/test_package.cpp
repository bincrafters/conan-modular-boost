#include <boost/python.hpp>
#include <cstdio>

namespace python = boost::python;

extern "C" void greet()
{
	std::puts("Greet.");
}

BOOST_PYTHON_MODULE(embedded_hello)
{
	python::def("greet",greet);
}


int main()
{
#  if PY_VERSION_HEX >= 0x03000000
    if (PyImport_AppendInittab("embedded_hello", PyInit_embedded_hello) == -1)
#else
    if (PyImport_AppendInittab("embedded_hello", initembedded_hello) == -1)
#endif
        throw std::runtime_error("Failed");
	Py_Initialize();

	python::object main = python::import("__main__");
	python::object global(main.attr("__dict__"));
	python::object result = python::exec(
		"from embedded_hello import *        \n"
		"greet()\n",
		global, global);
}
#include <cstdlib>
#include <iostream>

#include <boost/units/systems/si/electric_potential.hpp>
#include <boost/units/systems/si/current.hpp>
#include <boost/units/systems/si/resistance.hpp>
#include <boost/units/systems/si/io.hpp>

int main()
{
    using namespace boost::units;
    using namespace boost::units::si;

    quantity<current> I = 5 * amperes;
    quantity<resistance> R = 10 * ohms;

    std::cout << "I = " << I << std::endl;
    std::cout << "R = " << R << std::endl;
    std::cout << "U = I * R = " << I * R << std::endl;
    return EXIT_SUCCESS;
}

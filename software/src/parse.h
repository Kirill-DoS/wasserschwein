#include "arcanoid.h"
#include "constants.h"

#include <iostream>

// Разбирает старый C++-формат команды устройства; основной UART-парсер его не использует.
void parse(std::string expr){
    std::string dev = "";
    std::string num = "";
    size_t equalPos = expr.find(",");
    dev = expr.substr(0, equalPos);
    num = expr.substr(equalPos + 1);

    if(dev == "S1"){
        //std::cout<<"Start servo: " << dev << " on: " << std::stoi(num) <<'\n';
        esc_set_speed(SERVO1, std::stoi(num));
        printf("start %s on speed %s", dev, num);
    }
    else if(dev == "S2"){
        esc_set_speed(SERVO2, std::stoi(num));
        printf("Start %s on speed %s", dev, num);
        //std::cout<<"Start servo: " << dev << " on: " << std::stoi(num) <<'\n';
    }
    else if(dev == "M1"){
        //std::cout<<"Start motor: " << dev << " on: " << std::stoi(num) <<'\n';
        printf("Start %s on speed %s", dev, num);
    }
}



falcon_system_code = '''
#ifndef __FALCON_SYSTEM_DEFS__
#define __FALCON_SYSTEM_DEFS__

#include <stdint.h>
#include <fstream>
#include <stdio.h>
#include <stdlib.h>
#include <iostream>
#include <vector>
#include <stdexcept>


/**
 * @brief predefined data types for Falcon programming language
 * 
 * These types were chosen with the intent of being compatible with existing c/c++ codebases. 
 * Interger type names were/are inspired by the rust programming language
 *
 **/


/**
 * @brief Signed and unsigned 8-bit integers
 * 
 */
typedef unsigned char u8;
typedef signed char i8; 

/**
 * @brief Signed and unsigned 16-bit integers
 * 
 */
typedef unsigned short u16;
typedef signed short i16; 


/**
 * @brief Signed and unsigned 32-bit integers
 * 
 */
typedef unsigned int u32;
typedef signed int i32; 


/**
 * @brief Signed and unsigned 64-bit integers
 * 
 */
typedef unsigned long long u64;
typedef signed long long i64; 


/**
 * @brief 64-bit and 32-bit floating point real numbers
 * 
 */
typedef double f64; 
typedef float f32; 


/**
 * @brief boolean type
 * 
 */
typedef bool boolean; 


/**
 * @brief string type (OOP String for out-of-the-box features)
 * 
 */
typedef std::string string; 



/**
 * @brief File pointer | 
 * I chose to use the c version because in c++ we have to use different streams for reading and writing 
 * to files. 
 * 
 */
typedef FILE* file; 


/**
 * @brief null alias for compatability
 * 
 */
#define null (NULL)


template <typename Printable>
static i32 print(Printable message, ...) {
    std::cout << message; 
    return 0;
}


template <typename Listable>
void print(std::vector<Listable> msg) {
    print("["); 

    for (int x = 0; x < msg.size(); x++) {
        Listable t = msg.at(x);   
        if (x == msg.size()-1) {
            print(t);
            print("]"); 
            break;  
        }
        print(t); 
        print(", "); 
    }
}

template <typename Printable>
static i32 println(Printable message, ...) {
    std::cout << message << "\\n";
    return 0;
}

template <typename Listable>
void println(std::vector<Listable> msg) {
    print(msg); 
    println(" ");
}


#define logf(filePtr, ...) fprintf(filePtr, "%s: %d: %s(): fp @%p ", __FILE__, __LINE__, __func__, filePtr); print(__VA_ARGS__)
#define log(...) printf("%s: %d: %s():  ", __FILE__, __LINE__, __func__); std::cout << __VA_ARGS__ << std::endl
#define COLOR_ERROR "\\033[91m"
#define COLOR_CLEAR "\\033[0m"
#define COLOR_SUCCESS "\\033[92m"


template <typename Loopable>
i32 len(Loopable arr) {
    i32 s = 0; 
    for (auto i: arr) {
        s += 1;
    }

    return s;
}

static file open(string filename, string mode) {
    file fp = fopen(filename.c_str(), mode.c_str()); 
    if (fp == null) {
        logf(stderr, COLOR_ERROR "IO error:" COLOR_CLEAR " could not create or open file '%s'\\n", filename.c_str());
        exit(404);
    }
    return fp;
}

static string readfile(file fp) {
    fseek(fp, 1, SEEK_END); 
    size_t size = ftell(fp); 
    fseek(fp, 1, SEEK_SET); 

    char *buffer = (char *) malloc(size); 
    fread(buffer, size, 1, fp); 
    string result = string(buffer);
    free(buffer); 
    return result;
}

static string readline() {
    string result = string(""); 
    std::cin >> result; 
    return result; 
}

static i32 closefile(file fileptr) {
    if (fileptr == null) {
        logf(stderr, COLOR_ERROR "IO error:" COLOR_CLEAR " double free on closing file pointer ('%p')\\n", &fileptr);
        exit(408);
    }

    fclose(fileptr);
    return 0;
}


class FalconBase {
    public:
        string toString() {
            return "Object()";
        }
};

namespace range {

    #include <iostream>

    template <typename IntType>
    std::vector<IntType> range(IntType start, IntType stop, IntType step)
    {
    if (step == IntType(0))
    {
        throw std::invalid_argument("step for range must be non-zero");
    }

    std::vector<IntType> result;
    IntType i = start;
    while ((step > 0) ? (i < stop) : (i > stop))
    {
        result.push_back(i);
        i += step;
    }

    return result;
    }

    template <typename IntType>
    std::vector<IntType> range(IntType start, IntType stop)
    {
        if (start > stop) return range(start, stop - IntType(1), IntType(-1)); //for i in 200...0:
        return range(start, stop + IntType(1), IntType(1));
    }

    template <typename IntType>
    std::vector<IntType> range(IntType stop)
    {
    return range(IntType(0), stop, IntType(1));
    }
}


template <typename T>
std::vector<T> slice(std::vector<T> arr, int start, int end) {
    std::vector<T> ret; 
    int alen = arr.size(); 

    if (start < 0) {
        logf(stderr, COLOR_ERROR "Array index error:" COLOR_CLEAR "Array slice end point is out of range. index at %d", start);
        exit(512); 
    }

    if (end > alen) {
        logf(stderr, COLOR_ERROR "Array index error:" COLOR_CLEAR  "Array slice end point is out of range. index at %d", end);
        exit(512); 
    }

    for (; start <= end; start++) {
        ret.push_back(arr.at(start)); 
    }
    return ret;
}

std::string slice(std::string str, int start, int end) {
    std::string ret; 
    int alen = str.length();  

    if (start < 0) {
        logf(stderr, COLOR_ERROR "Array index error:" COLOR_CLEAR  "String slice start point is out of range. index at %d", end);
        exit(512); 
    }

    if (end > alen) {
        logf(stderr, COLOR_ERROR "Array index error:" COLOR_CLEAR  "String slice end point is out of range. index at %d", end);
        exit(100);
    }

    for (; start <= end; start++) {
        ret += str.at(start); 
    }
    return ret;   
}

#endif //__FALCON_SYSTEM_DEFS__
'''
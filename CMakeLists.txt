cmake_minimum_required(VERSION 3.20)

project(
  "demo-xml"
  VERSION 0.0.1
  LANGUAGES CXX)
add_executable(${PROJECT_NAME})
set_property(TARGET ${PROJECT_NAME} PROPERTY CXX_STANDARD 20)
set(CMAKE_INCLUDE_CURRENT_DIR ON)
set(BUILD_SHARED_LIBS ON)

# list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")
add_subdirectory("src")
install(TARGETS ${PROJECT_NAME})

#
# Log the pathname of the built target
#
if(EXISTS "${CMAKE_SOURCE_DIR}/scripts")
  get_property(_target_filename DIRECTORY ${CMAKE_SOURCE_DIR} PROPERTY BUILDSYSTEM_TARGETS)
  get_filename_component(_target_pathname ${_target_filename} REALPATH BASE_DIR ${CMAKE_BINARY_DIR})
  file(WRITE "scripts/target-pathname.txt" ${_target_pathname})
endif()

if(NOT CMAKE_BUILD_TYPE STREQUAL "Debug")
  target_compile_definitions(${PROJECT_NAME} PRIVATE NDEBUG)
endif()

if(PRESS_ENTER_TO_FINISH)
  target_compile_definitions(${PROJECT_NAME} PRIVATE PRESS_ENTER_TO_FINISH)
endif(PRESS_ENTER_TO_FINISH)

if(WIN32)
  target_compile_definitions(${PROJECT_NAME} PRIVATE
    VC_EXTRALEAN
    WIN32_LEAN_AND_MEAN
    _SCL_SECURE_NO_WARNINGS
    _CRT_SECURE_NO_WARNINGS
    _WINSOCK_DEPRECATED_NO_WARNINGS
    WINAPI_FAMILY=WINAPI_FAMILY_DESKTOP_APP
    _CONSOLE
    WINVER=0x0A00
    _WIN32_WINNT=0x0A00
  )
endif(WIN32)

if(MSVC)
  target_compile_options(${PROJECT_NAME} PRIVATE "/utf-8" "/Zc:wchar_t")
else()
  target_compile_options(${PROJECT_NAME} PRIVATE "-finput-charset=UTF-8")
endif()

#
# Dump of Preprocessor Output
#
if(PREPROCESSOR_DUMP_OUTPUT)
  if(MSVC)
    target_compile_options(${PROJECT_NAME} PRIVATE 
      -P # Preprocess to a File
      -C # Preserve Comments During Preprocessing
      -c # Compile Without Linking
    )
  else()
    target_compile_options(${PROJECT_NAME} PRIVATE -E)
  endif()
endif()

#
# Threads
#
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)
target_link_libraries(${PROJECT_NAME} PRIVATE Threads::Threads)

#
# Boost
#
set(Boost_NO_WARN_NEW_VERSIONS ON)
set(Boost_USE_MULTITHREADED ON)
set(Boost_USE_STATIC_LIBS OFF)
set(Boost_USE_STATIC_RUNTIME OFF)
set(Boost_USE_DEBUG_LIBS OFF)
set(Boost_USE_DEBUG_RUNTIME OFF)

if(WIN32)
  if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    message(STATUS "--> Using Boost debug libraries.")
    set(Boost_USE_DEBUG_LIBS ON)
    set(Boost_USE_DEBUG_RUNTIME ON)
  else()
    set(Boost_USE_RELEASE_LIBS ON)
    set(Boost_USE_RELEASE_RUNTIME ON)
  endif()
endif()

find_package(Boost REQUIRED COMPONENTS
  thread
  atomic
  filesystem iostreams
  regex
  log
  date_time
  chrono
  locale
  serialization
)

target_link_libraries(${PROJECT_NAME} PRIVATE Boost::boost)
target_link_libraries(${PROJECT_NAME} PRIVATE Boost::log)
target_link_libraries(${PROJECT_NAME} PRIVATE Boost::thread)
target_link_libraries(${PROJECT_NAME} PRIVATE Boost::atomic)
target_link_libraries(${PROJECT_NAME} PRIVATE Boost::locale)
target_link_libraries(${PROJECT_NAME} PRIVATE Boost::regex)
target_link_libraries(${PROJECT_NAME} PRIVATE Boost::date_time)
target_link_libraries(${PROJECT_NAME} PRIVATE Boost::filesystem)
target_link_libraries(${PROJECT_NAME} PRIVATE Boost::iostreams)
target_link_libraries(${PROJECT_NAME} PRIVATE Boost::chrono)
target_link_libraries(${PROJECT_NAME} PRIVATE Boost::serialization)
target_compile_definitions(
  Boost::boost
  INTERFACE
  BOOST_ALL_DYN_LINK
  BOOST_SYSTEM_NO_DEPRECATED
  BOOST_CONFIG_SUPPRESS_OUTDATED_MESSAGE
  _SILENCE_ALL_CXX17_DEPRECATION_WARNINGS
)

if(WIN32)
  target_compile_definitions(
    Boost::boost
    INTERFACE
    BOOST_SYSTEM_NO_LIB
    BOOST_USE_WINAPI_VERSION=0x0600
  )
endif()

if(NOT WIN32)
  # Support for <boost/dll.hpp> on Linux:
  target_link_libraries(${PROJECT_NAME} PUBLIC dl)
endif()

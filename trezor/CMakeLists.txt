cmake_minimum_required (VERSION 2.8)
project (decv)

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -pedantic -Wextra -Wwrite-strings -Wstrict-prototypes -Wmissing-prototypes -Wcast-qual -std=gnu11 -DPB_FIELD_16BIT")

add_subdirectory(trezor-crypto)

include_directories(include trezor-crypto)

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Werror -Wno-unknown-pragmas")

set(main_SRC
  "main.c"
)

add_executable(decv ${main_SRC})
target_link_libraries(decv TrezorCrypto)

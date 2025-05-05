Compiled on 2025-05-04 from neverwinter.nim/scriptcomp PR #147, ABI version 1.

These have been compiled with `zig c++`, like so:

for sys in macos windows linux; do
    for cpu in aarch64 x86_64; do
        mkdir -p src/nwn/nwscript/lib/${sys}_${cpu}
        case $sys in
            macos)
                ext="dylib"
                ;;
            linux)
                ext="so"
                ;;
            windows)
                ext="dll"
                ;;
        esac
        zig c++ -target ${cpu}-${sys} \
            -O2 -shared \
            -o abi/${sys}_${cpu}/libnwnscriptcomp.${ext} \
            neverwinter/nwscript/compilerapi.cpp \
            neverwinter/nwscript/native/*.{cpp,c}
    done
done

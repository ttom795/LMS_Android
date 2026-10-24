"""Assembles the Android Studio / Gradle project in port/android.

Usage: make_android.py SDL2_SRC DXVK_SRC DXVK_BUILD

  SDL2_SRC    an SDL2 2.30.x source tree (its android-project is the skeleton)
  DXVK_SRC    the patched dxvk-native tree (native-1.9.2b + optional-feature patch)
  DXVK_BUILD  a configured dxvk-native build dir (meson); its generated shader
              headers and compile_commands.json are reused, so the Android
              build needs neither meson nor glslang.

The native build (app/jni/CMakeLists.txt) compiles SDL2, dxvk's D3D9 and the
game (port/runtime + port/gen) for arm64-v8a.
"""
import json
import os
import shlex
import shutil
import sys

SDL, DXVK, DXVK_BUILD = sys.argv[1:4]
PORT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(PORT, "android")
PKG = "com.tj.legobatman"


def write(rel, text):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", newline="\n") as f:
        f.write(text)


def copytree(src, dst, ignore=None):
    dst = os.path.join(OUT, dst)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=ignore)


# ---- Gradle skeleton from SDL's android-project
ap = os.path.join(SDL, "android-project")
for rel in ["gradlew", "gradlew.bat", "gradle/wrapper/gradle-wrapper.jar",
            "gradle/wrapper/gradle-wrapper.properties", "gradle.properties", "build.gradle",
            "app/proguard-rules.pro", "app/src/main/res/values/colors.xml",
            "app/src/main/res/values/styles.xml"]:
    os.makedirs(os.path.dirname(os.path.join(OUT, rel)), exist_ok=True)
    shutil.copy(os.path.join(ap, rel), os.path.join(OUT, rel))
for d in os.listdir(os.path.join(ap, "app/src/main/res")):
    if d.startswith("mipmap"):
        copytree(os.path.join(ap, "app/src/main/res", d), "app/src/main/res/" + d)
copytree(os.path.join(ap, "app/src/main/java/org"), "app/src/main/java/org")
os.chmod(os.path.join(OUT, "gradlew"), 0o755)

write("settings.gradle", "rootProject.name = 'LegoBatman'\ninclude ':app'\n")
write("app/src/main/res/values/strings.xml",
      '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <string name="app_name">LEGO Batman</string>\n</resources>\n')

write("app/build.gradle", """apply plugin: 'com.android.application'

android {
    namespace "%(pkg)s"
    compileSdkVersion 34
    ndkVersion project.hasProperty('ndkVersion') ? project.property('ndkVersion') : null
    defaultConfig {
        applicationId "%(pkg)s"
        minSdkVersion 28
        targetSdkVersion 34
        versionCode 1
        versionName "0.1"
        externalNativeBuild {
            cmake {
                arguments "-DANDROID_STL=c++_shared", "-DANDROID_PLATFORM=android-28"
                abiFilters 'arm64-v8a'
            }
        }
    }
    buildTypes {
        // The recompiled game is large; debug builds would be unusably slow.
        debug {
            externalNativeBuild { cmake { arguments "-DCMAKE_BUILD_TYPE=Release" } }
            debuggable true
            jniDebuggable false
        }
        release {
            minifyEnabled false
            signingConfig signingConfigs.debug
        }
    }
    externalNativeBuild {
        cmake {
            path 'jni/CMakeLists.txt'
            version '3.22.1'
        }
    }
    packagingOptions {
        jniLibs { useLegacyPackaging true }
    }
    lint { abortOnError false }
}

dependencies {
    implementation fileTree(include: ['*.jar'], dir: 'libs')
}
""" % {"pkg": PKG})

write("app/src/main/AndroidManifest.xml", """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    android:versionCode="1" android:versionName="0.1" android:installLocation="auto">
    <uses-feature android:glEsVersion="0x00020000" />
    <uses-feature android:name="android.hardware.vulkan.version" android:version="0x401000" android:required="true" />
    <uses-feature android:name="android.hardware.touchscreen" android:required="false" />
    <uses-feature android:name="android.hardware.gamepad" android:required="false" />
    <uses-permission android:name="android.permission.VIBRATE" />
    <application android:label="@string/app_name" android:icon="@mipmap/ic_launcher"
        android:allowBackup="false" android:hardwareAccelerated="true"
        android:largeHeap="true" android:extractNativeLibs="true"
        android:theme="@android:style/Theme.NoTitleBar.Fullscreen">
        <activity android:name="LegoBatmanActivity" android:label="@string/app_name"
            android:alwaysRetainTaskState="true" android:launchMode="singleInstance"
            android:screenOrientation="sensorLandscape"
            android:configChanges="layoutDirection|locale|orientation|uiMode|screenLayout|screenSize|smallestScreenSize|keyboard|keyboardHidden|navigation"
            android:preferMinimalPostProcessing="true" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
""")

write("app/src/main/java/%s/LegoBatmanActivity.java" % PKG.replace(".", "/"), """package %s;

import org.libsdl.app.SDLActivity;

public class LegoBatmanActivity extends SDLActivity {
    @Override
    protected String[] getLibraries() {
        return new String[] { "SDL2", "dxvk_d3d9", "main" };
    }
}
""" % PKG)

# ---- native sources
copytree(SDL, "app/jni/SDL2", ignore=shutil.ignore_patterns(
    "android-project", "test", "Xcode", "VisualC*", "docs", "build-scripts", "cmake/test"))
# <SDL2/SDL.h> include style used by dxvk and the runtime
copytree(os.path.join(SDL, "include"), "app/jni/sdlinc/SDL2")

copytree(os.path.join(DXVK, "src"), "app/jni/dxvk/src",
         ignore=shutil.ignore_patterns("*.build"))
copytree(os.path.join(DXVK, "include"), "app/jni/dxvk/include")
gen = os.path.join(OUT, "app/jni/dxvk/generated")
os.makedirs(gen, exist_ok=True)
for root, _, files in os.walk(DXVK_BUILD):
    if "meson" in root:
        continue
    for fn in files:
        if fn.endswith(".h"):
            shutil.copy(os.path.join(root, fn), os.path.join(gen, fn))

srcs = []
for e in json.load(open(os.path.join(DXVK_BUILD, "compile_commands.json"))):
    f = os.path.normpath(os.path.join(e["directory"], e["file"]))
    rel = os.path.relpath(f, os.path.join(DXVK, "src"))
    srcs.append("src/" + rel.replace(os.sep, "/"))
write("app/jni/dxvk/CMakeLists.txt", """# dxvk-native D3D9 (native-1.9.2b, patched for mobile GPUs). Source list and
# generated shader headers come from a desktop meson build (tools/make_android.py).
add_library(dxvk_d3d9 SHARED
    %s)
target_include_directories(dxvk_d3d9 PRIVATE
    generated include include/native include/native/windows include/native/directx
    src/util src/dxvk src/d3d9 src/dxso src/wsi src/spirv src/vulkan ../sdlinc)
target_include_directories(dxvk_d3d9 PUBLIC include/native/directx include/native/windows include/native)
target_compile_definitions(dxvk_d3d9 PRIVATE NOMINMAX _WIN32_WINNT=0xa00 DXVK_NATIVE
    DXVK_WSI_SDL2 DXVK_PLATFORM_LINUX _FILE_OFFSET_BITS=64)
target_compile_options(dxvk_d3d9 PRIVATE -O2 "$<$<COMPILE_LANGUAGE:CXX>:SHELL:-include cstdint>" "$<$<COMPILE_LANGUAGE:CXX>:SHELL:-include cstring>"
    -Wno-deprecated-declarations -Wno-everything -fvisibility=default)
target_link_libraries(dxvk_d3d9 PRIVATE SDL2 vulkan $<$<BOOL:${ANDROID}>:log>)
""" % "\n    ".join(sorted(srcs)))

write("app/jni/CMakeLists.txt", """cmake_minimum_required(VERSION 3.18)
project(legobatman C CXX)
set(CMAKE_CXX_STANDARD 17)
# Each recompiled file needs 1-2 GB of RAM to compile; cap parallel jobs.
set(LB_GEN_JOBS 3 CACHE STRING "parallel compiles of recompiled code")
set_property(GLOBAL APPEND PROPERTY JOB_POOLS gen=${LB_GEN_JOBS})

set(SDL_SHARED ON CACHE BOOL "" FORCE)
set(SDL_STATIC OFF CACHE BOOL "" FORCE)
set(SDL_TEST OFF CACHE BOOL "" FORCE)
add_subdirectory(SDL2)
add_subdirectory(dxvk)
add_subdirectory(game)
""")

write("app/jni/game/CMakeLists.txt", """# The game: host runtime + recompiled code from port/runtime and port/gen.
get_filename_component(PORT ${CMAKE_CURRENT_SOURCE_DIR}/../../../.. ABSOLUTE)
file(GLOB GEN_SRC ${PORT}/gen/*.c)
file(GLOB RT_SRC ${PORT}/runtime/*.c)
file(GLOB RT_CXX ${PORT}/runtime/*.cpp)

add_library(lbgen OBJECT ${GEN_SRC})
set_property(TARGET lbgen PROPERTY JOB_POOL_COMPILE gen)
target_include_directories(lbgen PRIVATE ${PORT}/runtime ${PORT}/gen)
target_compile_options(lbgen PRIVATE -std=gnu11 -O1 -g0 -fno-strict-aliasing -fwrapv -w -fPIC)

add_library(main SHARED ${RT_SRC} ${RT_CXX} $<TARGET_OBJECTS:lbgen>)
target_include_directories(main PRIVATE ${PORT}/runtime ${PORT}/gen ../sdlinc
    ../dxvk/include/native/directx ../dxvk/include/native/windows ../dxvk/include/native)
target_compile_definitions(main PRIVATE DXVK_NATIVE)
target_compile_options(main PRIVATE -O2 -fno-strict-aliasing -fwrapv -Wno-everything
    $<$<COMPILE_LANGUAGE:C>:-std=gnu11>)
target_link_libraries(main PRIVATE SDL2 dxvk_d3d9 m $<$<BOOL:${ANDROID}>:log>)
""")
print("android project written to", OUT, "with", len(srcs), "dxvk sources")

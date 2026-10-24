package com.tj.legobatman;

import org.libsdl.app.SDLActivity;

public class LegoBatmanActivity extends SDLActivity {
    @Override
    protected String[] getLibraries() {
        return new String[] { "SDL2", "dxvk_d3d9", "main" };
    }
}

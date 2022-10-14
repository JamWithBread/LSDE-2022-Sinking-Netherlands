function hex2(c: number) {
    c = Math.round(c);
    if (c < 0) c = 0;
    if (c > 255) c = 255;
    let s = c.toString(16);
    if (s.length < 2) s = "0" + s;
    return s;
}

function rgb2hex(r: number, g: number, b:number) {
    return "#" + hex2(r) + hex2(g) + hex2(b);
}

function shade(baseColor: string, light: number): string {
    let r = parseInt(baseColor.substring(1, 3), 16);
    let g = parseInt(baseColor.substring(3, 5), 16);
    let b = parseInt(baseColor.substring(5, 7), 16);

    if (light < 0) {
        r = (1 + light) * r;
        g = (1 + light) * g;
        b = (1 + light) * b;
    } else {
        r = (1 - light) * r + light * 255;
        g = (1 - light) * g + light * 255;
        b = (1 - light) * b + light * 255;
    }

    return rgb2hex(r, g, b);
}

export {shade}

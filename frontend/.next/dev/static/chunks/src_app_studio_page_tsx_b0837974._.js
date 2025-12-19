(globalThis.TURBOPACK || (globalThis.TURBOPACK = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/src/app/studio/page.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>StudioPage
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$compiler$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/compiler-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
'use client';
;
;
function StudioPage() {
    _s();
    const $ = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$compiler$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["c"])(32);
    if ($[0] !== "71039948e6bb615357c8f7cfd1e66d2d43bad28e7129d4d27e3d1556f52ffb2c") {
        for(let $i = 0; $i < 32; $i += 1){
            $[$i] = Symbol.for("react.memo_cache_sentinel");
        }
        $[0] = "71039948e6bb615357c8f7cfd1e66d2d43bad28e7129d4d27e3d1556f52ffb2c";
    }
    let t0;
    if ($[1] === Symbol.for("react.memo_cache_sentinel")) {
        t0 = [
            "\u6700\u8FD1\u3001\u4F55\u304B\u306B\u77DB\u76FE\u3092\u611F\u3058\u305F\u3053\u3068\u306F\u3042\u308A\u307E\u3059\u304B\uFF1F",
            "\u305D\u306E\u77DB\u76FE\u3092\u89E3\u6C7A\u3059\u308B\u305F\u3081\u306B\u3001\u3069\u3093\u306A\u884C\u52D5\u3092\u3068\u308A\u307E\u3057\u305F\u304B\uFF1F",
            "\u52B4\u50CD\u306E\u4FA1\u5024\u306B\u3064\u3044\u3066\u3001\u3042\u306A\u305F\u306E\u8003\u3048\u3092\u6559\u3048\u3066\u304F\u3060\u3055\u3044\u3002",
            "\u4EBA\u9593\u6027\u3068\u601D\u8003\u306E\u5883\u754C\u7DDA\u306F\u3069\u3053\u306B\u3042\u308B\u3068\u601D\u3044\u307E\u3059\u304B\uFF1F",
            "\u672A\u6765\u306E\u60F3\u50CF\u529B\u304C\u6B20\u5982\u3057\u305F\u4E16\u754C\u306F\u3069\u3046\u306A\u308B\u3068\u601D\u3044\u307E\u3059\u304B\uFF1F",
            "\u81EA\u5DF1\u3068\u611F\u60C5\u3092\u5207\u308A\u96E2\u3057\u3066\u8003\u3048\u305F\u3053\u3068\u306F\u3042\u308A\u307E\u3059\u304B\uFF1F",
            "\u6559\u8A13\u3092\u5F97\u308B\u305F\u3081\u306B\u652F\u6255\u3063\u305F\u6700\u5927\u306E\u4EE3\u511F\u306F\u4F55\u3067\u3059\u304B\uFF1F",
            "\u6700\u5F8C\u306B\u3001\u3053\u306E\u30C6\u30FC\u30DE\u306E\u7D50\u8AD6\u309230\u79D2\u3067\u307E\u3068\u3081\u3066\u304F\u3060\u3055\u3044\u3002"
        ];
        $[1] = t0;
    } else {
        t0 = $[1];
    }
    const [questions] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(t0);
    const [currentIndex, setCurrentIndex] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(0);
    let t1;
    if ($[2] !== currentIndex || $[3] !== questions.length) {
        t1 = ({
            "StudioPage[handleNext]": ()=>{
                if (currentIndex < questions.length - 1) {
                    setCurrentIndex(currentIndex + 1);
                } else {
                    alert("\u3059\u3079\u3066\u306E\u53CE\u9332\u304C\u5B8C\u4E86\u3057\u307E\u3057\u305F\uFF01");
                }
            }
        })["StudioPage[handleNext]"];
        $[2] = currentIndex;
        $[3] = questions.length;
        $[4] = t1;
    } else {
        t1 = $[4];
    }
    const handleNext = t1;
    const t2 = currentIndex + 1;
    let t3;
    if ($[5] !== t2) {
        t3 = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "absolute top-[-20px] left-[-20px] text-[200px] font-black text-slate-50 opacity-[0.03] pointer-events-none",
            children: t2
        }, void 0, false, {
            fileName: "[project]/src/app/studio/page.tsx",
            lineNumber: 43,
            columnNumber: 10
        }, this);
        $[5] = t2;
        $[6] = t3;
    } else {
        t3 = $[6];
    }
    const t4 = currentIndex + 1;
    let t5;
    if ($[7] !== questions.length || $[8] !== t4) {
        t5 = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
            className: "px-4 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs font-black tracking-widest",
            children: [
                "STEP ",
                t4,
                " / ",
                questions.length
            ]
        }, void 0, true, {
            fileName: "[project]/src/app/studio/page.tsx",
            lineNumber: 52,
            columnNumber: 10
        }, this);
        $[7] = questions.length;
        $[8] = t4;
        $[9] = t5;
    } else {
        t5 = $[9];
    }
    let t6;
    if ($[10] !== currentIndex || $[11] !== questions) {
        let t7;
        if ($[13] !== currentIndex) {
            t7 = ({
                "StudioPage[questions.map()]": (_, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: `h-1 w-6 rounded-full ${i <= currentIndex ? "bg-emerald-500" : "bg-slate-100"}`
                    }, i, false, {
                        fileName: "[project]/src/app/studio/page.tsx",
                        lineNumber: 64,
                        columnNumber: 50
                    }, this)
            })["StudioPage[questions.map()]"];
            $[13] = currentIndex;
            $[14] = t7;
        } else {
            t7 = $[14];
        }
        t6 = questions.map(t7);
        $[10] = currentIndex;
        $[11] = questions;
        $[12] = t6;
    } else {
        t6 = $[12];
    }
    let t7;
    if ($[15] !== t6) {
        t7 = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "flex gap-1",
            children: t6
        }, void 0, false, {
            fileName: "[project]/src/app/studio/page.tsx",
            lineNumber: 80,
            columnNumber: 10
        }, this);
        $[15] = t6;
        $[16] = t7;
    } else {
        t7 = $[16];
    }
    let t8;
    if ($[17] !== t5 || $[18] !== t7) {
        t8 = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "flex items-center justify-between mb-12",
            children: [
                t5,
                t7
            ]
        }, void 0, true, {
            fileName: "[project]/src/app/studio/page.tsx",
            lineNumber: 88,
            columnNumber: 10
        }, this);
        $[17] = t5;
        $[18] = t7;
        $[19] = t8;
    } else {
        t8 = $[19];
    }
    const t9 = questions[currentIndex];
    let t10;
    if ($[20] !== t9) {
        t10 = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
            className: "text-5xl font-extrabold text-slate-800 mb-16 leading-[1.3] min-h-[200px] flex items-center",
            children: t9
        }, void 0, false, {
            fileName: "[project]/src/app/studio/page.tsx",
            lineNumber: 98,
            columnNumber: 11
        }, this);
        $[20] = t9;
        $[21] = t10;
    } else {
        t10 = $[21];
    }
    const t11 = currentIndex === questions.length - 1 ? "\u53CE\u9332\u5B8C\u4E86" : "\u56DE\u7B54\u5B8C\u4E86\u3001\u6B21\u306E\u8CEA\u554F\u3078";
    let t12;
    if ($[22] !== handleNext || $[23] !== t11) {
        t12 = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
            onClick: handleNext,
            className: "w-full bg-slate-900 text-white py-8 rounded-3xl font-black text-2xl hover:bg-emerald-600 transition-all transform hover:-translate-y-1 active:scale-95 shadow-2xl shadow-slate-200",
            children: t11
        }, void 0, false, {
            fileName: "[project]/src/app/studio/page.tsx",
            lineNumber: 107,
            columnNumber: 11
        }, this);
        $[22] = handleNext;
        $[23] = t11;
        $[24] = t12;
    } else {
        t12 = $[24];
    }
    let t13;
    if ($[25] !== t10 || $[26] !== t12 || $[27] !== t8) {
        t13 = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "relative",
            children: [
                t8,
                t10,
                t12
            ]
        }, void 0, true, {
            fileName: "[project]/src/app/studio/page.tsx",
            lineNumber: 116,
            columnNumber: 11
        }, this);
        $[25] = t10;
        $[26] = t12;
        $[27] = t8;
        $[28] = t13;
    } else {
        t13 = $[28];
    }
    let t14;
    if ($[29] !== t13 || $[30] !== t3) {
        t14 = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "p-12 flex flex-col items-center justify-center min-h-[80vh]",
            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "max-w-4xl w-full bg-white p-20 rounded-[50px] shadow-[0_20px_60px_-15px_rgba(0,0,0,0.1)] border border-slate-100 relative overflow-hidden",
                children: [
                    t3,
                    t13
                ]
            }, void 0, true, {
                fileName: "[project]/src/app/studio/page.tsx",
                lineNumber: 126,
                columnNumber: 88
            }, this)
        }, void 0, false, {
            fileName: "[project]/src/app/studio/page.tsx",
            lineNumber: 126,
            columnNumber: 11
        }, this);
        $[29] = t13;
        $[30] = t3;
        $[31] = t14;
    } else {
        t14 = $[31];
    }
    return t14;
}
_s(StudioPage, "qv9YKq/kqapJ8Ecpf50QMjyvruI=");
_c = StudioPage;
var _c;
__turbopack_context__.k.register(_c, "StudioPage");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
]);

//# sourceMappingURL=src_app_studio_page_tsx_b0837974._.js.map
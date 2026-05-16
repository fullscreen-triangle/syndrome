/**
 * webgl.js — WebGL 2.0 helpers for GPU-accelerated spectral comparison.
 *
 * The fragment shader implements the immunological primitive:
 *   each fragment ≡ one (query, target) pair
 *   gl_FragColor.r = dot(queryEmb, targetEmb[fragCoord.x])
 *
 * This is equivalent to a parallel matched-filter bank:
 * O(dN) total work, bandwidth-limited, no serial bottleneck.
 */

/**
 * Initialize a WebGL2 context on a canvas element.
 * Returns null if WebGL2 is unavailable (fallback to JS).
 */
function initGL(canvas) {
  const gl = canvas.getContext('webgl2');
  if (!gl) return null;
  gl.getExtension('EXT_color_buffer_float');
  return gl;
}

/**
 * Compile a shader program from vertex + fragment source strings.
 */
function compileProgram(gl, vertSrc, fragSrc) {
  function compile(type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      throw new Error('Shader compile error: ' + gl.getShaderInfoLog(s));
    }
    return s;
  }
  const prog = gl.createProgram();
  gl.attachShader(prog, compile(gl.VERTEX_SHADER, vertSrc));
  gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, fragSrc));
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
    throw new Error('Program link error: ' + gl.getProgramInfoLog(prog));
  }
  return prog;
}

/**
 * Upload a Float32Array as a 1D RGBA32F texture of width=length/4.
 * Used to pack embedding arrays into texture memory.
 */
function uploadTexture1D(gl, data, width) {
  const tex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA32F, width, 1, 0,
                gl.RGBA, gl.FLOAT, data);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  return tex;
}

/**
 * Upload a 2D Float32Array (rows × cols packed RGBA) as a 2D RGBA32F texture.
 * rows = number of targets, cols = embeddingDim / 4.
 * The fragment shader reads row i as the embedding for target i.
 */
function uploadTexture2D(gl, data, width, height) {
  const tex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA32F, width, height, 0,
                gl.RGBA, gl.FLOAT, data);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  return tex;
}

/**
 * Create a framebuffer with an RGBA32F color attachment of given dimensions.
 * Used as the render target for readback of dot-product results.
 */
function createFramebuffer(gl, width, height) {
  const tex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA32F, width, height, 0,
                gl.RGBA, gl.FLOAT, null);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);

  const fb = gl.createFramebuffer();
  gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0,
                          gl.TEXTURE_2D, tex, 0);
  return { fb, tex };
}

/**
 * GLSL source: full-screen quad vertex shader (clip-space triangle strip).
 */
const QUAD_VERT = `#version 300 es
in vec2 a_pos;
out vec2 v_uv;
void main() {
  v_uv = (a_pos + 1.0) * 0.5;
  gl_Position = vec4(a_pos, 0.0, 1.0);
}`;

/**
 * Upload the full-screen quad geometry.
 */
function createQuad(gl, prog) {
  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER,
    new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(prog, 'a_pos');
  const vao = gl.createVertexArray();
  gl.bindVertexArray(vao);
  gl.enableVertexAttribArray(loc);
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  gl.bindVertexArray(null);
  return vao;
}

/**
 * GLSL fragment shader: computes dot(query_emb, target_emb[x])
 * for all targets packed in u_targets texture.
 *
 * Layout:
 *   u_query:   sampler2D, 1×(D/4) RGBA32F — query embedding (D = embDim)
 *   u_targets: sampler2D, (D/4)×N RGBA32F — N target embeddings, each D-dim
 *   u_N:       int — number of targets
 *   u_D4:      int — D/4 (texture width)
 *
 * Output: red channel = similarity ρ ∈ [-1,1]
 */
function dotProductFragSrc(D) {
  const D4 = Math.ceil(D / 4);
  return `#version 300 es
precision highp float;
precision highp sampler2D;

uniform sampler2D u_query;
uniform sampler2D u_targets;
uniform int u_N;

out vec4 fragColor;
in vec2 v_uv;

void main() {
  int targetIdx = int(v_uv.x * float(u_N));
  if (targetIdx >= u_N) { fragColor = vec4(0.0); return; }

  float dot_val = 0.0;
  int D4 = ${D4};
  for (int i = 0; i < D4; i++) {
    vec4 q = texelFetch(u_query,   ivec2(i, 0), 0);
    vec4 t = texelFetch(u_targets, ivec2(i, targetIdx), 0);
    dot_val += dot(q, t);
  }
  fragColor = vec4(dot_val, 0.0, 0.0, 1.0);
}`;
}

/**
 * GPU-accelerated batch similarity computation.
 *
 * @param {WebGL2RenderingContext} gl
 * @param {Float32Array} queryEmb    — embedding of query, length D
 * @param {Float32Array[]} targetEmbs — array of N target embeddings, each length D
 * @returns {Float32Array} similarities — length N, ρ ∈ [-1,1]
 */
function gpuBatchSimilarity(gl, queryEmb, targetEmbs) {
  const D = queryEmb.length;
  const D4 = Math.ceil(D / 4);
  const N = targetEmbs.length;

  // Pack query into 1×D4 RGBA texture (pad to multiple of 4)
  const queryPadded = new Float32Array(D4 * 4);
  queryPadded.set(queryEmb);

  // Pack targets into N×D4 RGBA texture (each row = one target)
  const targetData = new Float32Array(N * D4 * 4);
  for (let i = 0; i < N; i++) {
    const src = targetEmbs[i];
    for (let j = 0; j < src.length; j++) targetData[i * D4 * 4 + j] = src[j];
  }

  const prog = compileProgram(gl, QUAD_VERT, dotProductFragSrc(D));
  const vao = createQuad(gl, prog);
  const qTex = uploadTexture2D(gl, queryPadded, D4, 1);
  const tTex = uploadTexture2D(gl, targetData, D4, N);
  const { fb } = createFramebuffer(gl, N, 1);

  gl.useProgram(prog);
  gl.viewport(0, 0, N, 1);
  gl.bindFramebuffer(gl.FRAMEBUFFER, fb);

  gl.activeTexture(gl.TEXTURE0);
  gl.bindTexture(gl.TEXTURE_2D, qTex);
  gl.uniform1i(gl.getUniformLocation(prog, 'u_query'), 0);

  gl.activeTexture(gl.TEXTURE1);
  gl.bindTexture(gl.TEXTURE_2D, tTex);
  gl.uniform1i(gl.getUniformLocation(prog, 'u_targets'), 1);
  gl.uniform1i(gl.getUniformLocation(prog, 'u_N'), N);

  gl.bindVertexArray(vao);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

  const result = new Float32Array(N * 4);
  gl.readPixels(0, 0, N, 1, gl.RGBA, gl.FLOAT, result);

  const sims = new Float32Array(N);
  for (let i = 0; i < N; i++) sims[i] = result[i * 4];
  return sims;
}

export { initGL, compileProgram, uploadTexture1D, uploadTexture2D,
         createFramebuffer, createQuad, gpuBatchSimilarity,
         QUAD_VERT, dotProductFragSrc };

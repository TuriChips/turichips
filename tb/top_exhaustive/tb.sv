// Acceptance test 1 (spec §6): all 2^14 = 16384 combinations of (a, b, s, m, cn_n),
// every output compared against the spec §3 equations. Covers B1, B3, B4, B5, B8.
module tb;
  logic [3:0] a, b, s;
  logic       m, cn_n;
  wire  [3:0] f;
  wire        cn4_n, x, y, aeqb;
  top dut (.a(a), .b(b), .s(s), .m(m), .cn_n(cn_n),
           .f(f), .cn4_n(cn4_n), .x(x), .y(y), .aeqb(aeqb));

  logic [3:0] p, g, h, c_chain, ef;
  logic [4:0] c;
  logic       ecn4_n, ex, ey, eaeqb;
  integer errors = 0, checks = 0;

  initial begin
    for (int n = 0; n < 16384; n++) begin
      {s, m, cn_n, a, b} = n[13:0];
      #1;
      // Spec §3, transcribed line by line.
      for (int i = 0; i < 4; i++) begin
        p[i] = a[i] | (b[i] & s[0]) | (~b[i] & s[1]);
        g[i] = (a[i] & ~b[i] & s[2]) | (a[i] & b[i] & s[3]);
        h[i] = p[i] & ~g[i];
      end
      c[0] = ~cn_n;
      for (int i = 0; i < 4; i++) c[i+1] = g[i] | (p[i] & c[i]);
      c_chain = c[3:0];
      for (int i = 0; i < 4; i++) ef[i] = m ? ~h[i] : (h[i] ^ c_chain[i]);
      ecn4_n = ~c[4];
      ex     = g[0] | g[1] | g[2] | g[3];
      ey     = ~(~p[3] | (~g[3] & ~p[2]) | (~g[3] & ~g[2] & ~p[1]) | (~g[3] & ~g[2] & ~g[1] & ~p[0]));
      eaeqb  = &ef;
      checks++;
      if ($isunknown({f, cn4_n, x, y, aeqb})) begin
        errors++;
        if (errors <= 10) $display("FAIL B8 X/Z: a=%b b=%b s=%b m=%b cn_n=%b", a, b, s, m, cn_n);
      end else if (f !== ef || cn4_n !== ecn4_n || x !== ex || y !== ey || aeqb !== eaeqb) begin
        errors++;
        if (errors <= 10)
          $display("FAIL a=%b b=%b s=%b m=%b cn_n=%b: got f=%b cn4_n=%b x=%b y=%b aeqb=%b, expected f=%b cn4_n=%b x=%b y=%b aeqb=%b",
                   a, b, s, m, cn_n, f, cn4_n, x, y, aeqb, ef, ecn4_n, ex, ey, eaeqb);
      end
    end
    // B4: x and y do not depend on m or cn_n (checked directly, independent of the equations above).
    for (int n = 0; n < 256; n++)
      for (int sv = 0; sv < 16; sv++) begin
        logic rx, ry;
        a = n[7:4]; b = n[3:0]; s = sv[3:0];
        m = 1'b0; cn_n = 1'b0; #1; rx = x; ry = y;
        for (int k = 1; k < 4; k++) begin
          m = k[0]; cn_n = k[1]; #1;
          checks++;
          if (x !== rx || y !== ry) begin
            errors++;
            if (errors <= 10) $display("FAIL B4 x/y depend on m or cn_n: a=%b b=%b s=%b", a, b, s);
          end
        end
      end
    if (errors == 0) $display("PASS top_exhaustive: %0d checks, 0 mismatches", checks);
    else $fatal(1, "FAIL top_exhaustive: %0d mismatches in %0d checks", errors, checks);
    $finish;
  end
endmodule

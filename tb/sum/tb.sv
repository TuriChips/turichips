// Block test: alu181_sum against spec §3 (f). All (p, g, c, m) with g[i] implying p[i].
module tb;
  logic [3:0] p, g, c;
  logic       m;
  wire  [3:0] f;
  alu181_sum dut (.p(p), .g(g), .c(c), .m(m), .f(f));
  logic [3:0] h, ef;
  integer errors = 0, checks = 0;
  initial begin
    for (int n = 0; n < 8192; n++) begin
      {m, c, p, g} = n[12:0];
      if ((g & ~p) == 4'b0000) begin
        #1;
        h = p & ~g;
        for (int i = 0; i < 4; i++) ef[i] = m ? ~h[i] : (h[i] ^ c[i]);
        checks++;
        if (f !== ef) begin
          errors++;
          if (errors <= 10) $display("FAIL p=%b g=%b c=%b m=%b: got f=%b, expected f=%b", p, g, c, m, f, ef);
        end
      end
    end
    if (errors == 0) $display("PASS sum: %0d checks, 0 mismatches", checks);
    else $fatal(1, "FAIL sum: %0d mismatches in %0d checks", errors, checks);
    $finish;
  end
endmodule

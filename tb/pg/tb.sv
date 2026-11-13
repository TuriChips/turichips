// Block test: alu181_pg against spec §3 (p, g). All 2^12 (a, b, s) combinations.
module tb;
  logic [3:0] a, b, s;
  wire  [3:0] p, g;
  alu181_pg dut (.a(a), .b(b), .s(s), .p(p), .g(g));
  logic [3:0] ep, eg;
  integer errors = 0, checks = 0;
  initial begin
    for (int n = 0; n < 4096; n++) begin
      {s, a, b} = n[11:0]; #1;
      for (int i = 0; i < 4; i++) begin
        ep[i] = a[i] | (b[i] & s[0]) | (~b[i] & s[1]);
        eg[i] = (a[i] & ~b[i] & s[2]) | (a[i] & b[i] & s[3]);
      end
      checks++;
      if (p !== ep || g !== eg) begin
        errors++;
        if (errors <= 10) $display("FAIL a=%b b=%b s=%b: got p=%b g=%b, expected p=%b g=%b", a, b, s, p, g, ep, eg);
      end
    end
    if (errors == 0) $display("PASS pg: %0d checks, 0 mismatches", checks);
    else $fatal(1, "FAIL pg: %0d mismatches in %0d checks", errors, checks);
    $finish;
  end
endmodule

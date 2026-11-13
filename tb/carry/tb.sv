// Block test: alu181_carry against spec §3 (c, cn4_n, x, y).
// Inputs: all (p, g, cn_n) with g[i] implying p[i] (the spec guarantees this relation;
// other inputs cannot occur, so their behaviour is not specified or tested).
module tb;
  logic [3:0] p, g;
  logic       cn_n;
  wire  [3:0] c;
  wire        cn4_n, x, y;
  alu181_carry dut (.p(p), .g(g), .cn_n(cn_n), .c(c), .cn4_n(cn4_n), .x(x), .y(y));
  logic [4:0] ec;
  logic       ex, ey;
  integer errors = 0, checks = 0;
  initial begin
    for (int n = 0; n < 512; n++) begin
      {p, g, cn_n} = n[8:0];
      if ((g & ~p) == 4'b0000) begin
        #1;
        ec[0] = ~cn_n;
        for (int i = 0; i < 4; i++) ec[i+1] = g[i] | (p[i] & ec[i]);
        ex = g[0] | g[1] | g[2] | g[3];
        ey = ~(~p[3] | (~g[3] & ~p[2]) | (~g[3] & ~g[2] & ~p[1]) | (~g[3] & ~g[2] & ~g[1] & ~p[0]));
        checks++;
        if (c !== ec[3:0] || cn4_n !== ~ec[4] || x !== ex || y !== ey) begin
          errors++;
          if (errors <= 10)
            $display("FAIL p=%b g=%b cn_n=%b: got c=%b cn4_n=%b x=%b y=%b, expected c=%b cn4_n=%b x=%b y=%b",
                     p, g, cn_n, c, cn4_n, x, y, ec[3:0], ~ec[4], ex, ey);
        end
      end
    end
    if (errors == 0) $display("PASS carry: %0d checks, 0 mismatches", checks);
    else $fatal(1, "FAIL carry: %0d mismatches in %0d checks", errors, checks);
    $finish;
  end
endmodule

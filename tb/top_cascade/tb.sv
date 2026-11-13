// B7 (spec §5) / acceptance test 3: two 74181s, cn4_n of the low chip wired to cn_n of
// the high chip, as an 8-bit adder (A+B) and subtractor (A-B), all 65536 operand pairs.
module tb;
  logic [7:0] A, B;
  logic       m, cn_in_n;
  logic [3:0] s;
  wire  [3:0] f_lo, f_hi;
  wire        c_mid_n, c_out_n;
  /* verilator lint_off UNUSEDSIGNAL */
  wire        x_lo, y_lo, x_hi, y_hi, eq_lo, eq_hi;
  /* verilator lint_on UNUSEDSIGNAL */

  top lo (.a(A[3:0]), .b(B[3:0]), .s(s), .m(m), .cn_n(cn_in_n),
          .f(f_lo), .cn4_n(c_mid_n), .x(x_lo), .y(y_lo), .aeqb(eq_lo));
  top hi (.a(A[7:4]), .b(B[7:4]), .s(s), .m(m), .cn_n(c_mid_n),
          .f(f_hi), .cn4_n(c_out_n), .x(x_hi), .y(y_hi), .aeqb(eq_hi));

  integer errors = 0, checks = 0;
  logic [8:0] sum;
  logic [7:0] diff;

  initial begin
    m = 1'b0;
    for (int ai = 0; ai < 256; ai++)
      for (int bi = 0; bi < 256; bi++) begin
        A = ai[7:0]; B = bi[7:0];
        // Add: s=1001, no carry in (cn_n=1). Expect A+B, carry out (cn4_n=0) when sum > 255.
        s = 4'b1001; cn_in_n = 1'b1; #1;
        sum = {1'b0, A} + {1'b0, B};
        checks++;
        if ({f_hi, f_lo} !== sum[7:0] || c_out_n !== ~sum[8]) begin
          errors++;
          if (errors <= 10) $display("FAIL add A=%0d B=%0d: got %0d cout_n=%b, expected %0d cout=%b",
                                     A, B, {f_hi, f_lo}, c_out_n, sum[7:0], sum[8]);
        end
        // Subtract: s=0110, cn_n=0 gives A-B (spec §4). Expect A-B mod 256.
        s = 4'b0110; cn_in_n = 1'b0; #1;
        diff = A - B;
        checks++;
        if ({f_hi, f_lo} !== diff) begin
          errors++;
          if (errors <= 10) $display("FAIL sub A=%0d B=%0d: got %0d, expected %0d", A, B, {f_hi, f_lo}, diff);
        end
      end
    if (errors == 0) $display("PASS top_cascade: %0d checks, 0 mismatches", checks);
    else $fatal(1, "FAIL top_cascade: %0d mismatches in %0d checks", errors, checks);
    $finish;
  end
endmodule

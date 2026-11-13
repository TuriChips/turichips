// Acceptance test 2 (spec §6): TI function table (spec §4), all rows, both modes.
// Also covers B1, B2, B5, B6, B8 and the B3 worked example.
// Expected values come from the spec §4 table only, not from the §3 equations.
module tb;
  logic [3:0] a, b, s;
  logic       m, cn_n;
  wire  [3:0] f;
  wire        cn4_n, x, y, aeqb;
  top dut (.a(a), .b(b), .s(s), .m(m), .cn_n(cn_n),
           .f(f), .cn4_n(cn4_n), .x(x), .y(y), .aeqb(aeqb));

  // Spec §4, m=1 column.
  function automatic logic [3:0] t_logic(input logic [3:0] s_i, a_i, b_i);
    case (s_i)
      4'b0000: t_logic = ~a_i;
      4'b0001: t_logic = ~(a_i | b_i);
      4'b0010: t_logic = ~a_i & b_i;
      4'b0011: t_logic = 4'b0000;
      4'b0100: t_logic = ~(a_i & b_i);
      4'b0101: t_logic = ~b_i;
      4'b0110: t_logic = a_i ^ b_i;
      4'b0111: t_logic = a_i & ~b_i;
      4'b1000: t_logic = ~a_i | b_i;
      4'b1001: t_logic = ~(a_i ^ b_i);
      4'b1010: t_logic = b_i;
      4'b1011: t_logic = a_i & b_i;
      4'b1100: t_logic = 4'b1111;
      4'b1101: t_logic = a_i | ~b_i;
      4'b1110: t_logic = a_i | b_i;
      default: t_logic = a_i;
    endcase
  endfunction

  // Spec §4, m=0, cn_n=1 column. The cn_n=0 column is this value + 1 (mod 16).
  function automatic logic [3:0] t_arith(input logic [3:0] s_i, a_i, b_i);
    logic [3:0] t1, t2;
    begin
      t1 = a_i & ~b_i;  t2 = a_i & b_i;
      case (s_i)
        4'b0000: t_arith = a_i;
        4'b0001: t_arith = a_i | b_i;
        4'b0010: t_arith = a_i | ~b_i;
        4'b0011: t_arith = 4'b1111;
        4'b0100: t_arith = a_i + t1;
        4'b0101: t_arith = (a_i | b_i) + t1;
        4'b0110: t_arith = a_i - b_i - 4'd1;
        4'b0111: t_arith = t1 - 4'd1;
        4'b1000: t_arith = a_i + t2;
        4'b1001: t_arith = a_i + b_i;
        4'b1010: t_arith = (a_i | ~b_i) + t2;
        4'b1011: t_arith = t2 - 4'd1;
        4'b1100: t_arith = a_i + a_i;
        4'b1101: t_arith = (a_i | b_i) + a_i;
        4'b1110: t_arith = (a_i | ~b_i) + a_i;
        default: t_arith = a_i - 4'd1;
      endcase
    end
  endfunction

  integer errors = 0, checks = 0;
  logic [3:0] exp_f;
  logic [3:0] fa, fb;

  task automatic fail(input string msg);
    errors++;
    if (errors <= 10)
      $display("FAIL %s: a=%b b=%b s=%b m=%b cn_n=%b -> f=%b cn4_n=%b aeqb=%b (expected f=%b)",
               msg, a, b, s, m, cn_n, f, cn4_n, aeqb, exp_f);
  endtask

  initial begin
    for (int si = 0; si < 16; si++)
      for (int mi = 0; mi < 2; mi++)
        for (int ci = 0; ci < 2; ci++)
          for (int ai = 0; ai < 16; ai++)
            for (int bi = 0; bi < 16; bi++) begin
              s = si[3:0]; m = mi[0]; cn_n = ci[0]; a = ai[3:0]; b = bi[3:0];
              #1;
              if (m) exp_f = t_logic(s, a, b);
              else   exp_f = t_arith(s, a, b) + {3'b000, ~cn_n};
              checks++;
              // B8: fully driven inputs give no X/Z on any output.
              if ($isunknown({f, cn4_n, x, y, aeqb})) fail("B8 X/Z on output");
              else begin
                if (f !== exp_f) fail("B1 f mismatch");
                // B5: aeqb is 1 exactly when f == 1111.
                if (aeqb !== (f === 4'b1111)) fail("B5 aeqb");
              end
            end
    // B2: logic mode ignores cn_n.
    for (int si = 0; si < 16; si++)
      for (int ai = 0; ai < 16; ai++)
        for (int bi = 0; bi < 16; bi++) begin
          s = si[3:0]; m = 1'b1; a = ai[3:0]; b = bi[3:0];
          cn_n = 1'b0; #1; fa = f;
          cn_n = 1'b1; #1; fb = f;
          checks++;
          if (fa !== fb) begin exp_f = fa; fail("B2 f depends on cn_n in logic mode"); end
        end
    // B6: comparator, s=0110, m=0, cn_n=1: aeqb == (a == b).
    for (int ai = 0; ai < 16; ai++)
      for (int bi = 0; bi < 16; bi++) begin
        s = 4'b0110; m = 1'b0; cn_n = 1'b1; a = ai[3:0]; b = bi[3:0]; #1;
        exp_f = a - b - 4'd1;
        checks++;
        if (aeqb !== (a == b)) fail("B6 comparator");
      end
    // B3 worked example: A=1111, B=0001, s=1001, m=0, cn_n=1 -> f=0000, cn4_n=0.
    a = 4'b1111; b = 4'b0001; s = 4'b1001; m = 1'b0; cn_n = 1'b1; #1;
    exp_f = 4'b0000; checks++;
    if (f !== 4'b0000 || cn4_n !== 1'b0) fail("B3 example");
    // B3, comparator table (TI datasheet, via spec §9): s=0110, m=0.
    //   cn_n=1: cn4_n=1 when A<=B, 0 when A>B.  cn_n=0: cn4_n=1 when A<B, 0 when A>=B.
    for (int ci = 0; ci < 2; ci++)
      for (int ai = 0; ai < 16; ai++)
        for (int bi = 0; bi < 16; bi++) begin
          s = 4'b0110; m = 1'b0; cn_n = ci[0]; a = ai[3:0]; b = bi[3:0]; #1;
          exp_f = {3'b000, (ci == 1) ? (a <= b) : (a < b)};  // shown only as expected cn4_n in bit 0
          checks++;
          if (cn4_n !== ((ci == 1) ? (a <= b) : (a < b))) fail("B3 comparator cn4_n (exp shown in f bit0)");
        end
    if (errors == 0) $display("PASS top_table: %0d checks, 0 mismatches", checks);
    else $fatal(1, "FAIL top_table: %0d mismatches in %0d checks", errors, checks);
    $finish;
  end
endmodule

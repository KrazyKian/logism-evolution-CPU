//computes the dot product of two length 3 vectors
//the vectors in memory are <10, 20, 30> and <3, 5, 7>. THe output should be 340, which is 154 in hex
mov x8 3    //counter for dot product
ADR x2 vec1
ADR x4 vec2
mov x5 0    //offset i for vectors
mov x3 0    //accumulator
start:
    cbz x8 end      //check for loop end
    ldr x0 [x2, x5] //load ith entry of virst vector
    ldr x1 [x4, x5] //load ith entry of second vector
    add x5 x5 8     //increment offset i
    sub x8 x8 1     //decrement counter
    bl proc         //multiply x0 and x1
    add x3 x3 x0    //accumulate
    b start         //jump back to start
end:
str x3 [x31, 0] //stores result in memory location 0
mov x0 x3       //stores result in the LEDoutput register
stop            //displays LEDoutput register and halts the program





proc: //multiplies x0 and x1 and returns the product
    mul x0 x0 x1
    RET


.data
a: .byte 1
vec1: .quad 10, 20, 30
vec2: .quad 3, 5, 7

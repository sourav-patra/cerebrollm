for i in 1 2 3 4 5 6 7 8 9 10; do
curl -s -o /dev/null http://127.0.0.1:11434/api/embed -d '{"model":"bge-m3","input":["a b c","d e f","a b c1","d e f2","a b c3","d e f4","a b c5","d e f6","a b c7","d e f8","a b c9","d e f10","a b c11","d e f12","a b c13","d e f14"],"options":{"num_ctx":8192}}'
done

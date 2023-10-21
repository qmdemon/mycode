package main

import (
	"flag"
	"fmt"
	"net"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"
)

// 执行进度
var count = 0
var rundata = 0

var lock sync.RWMutex

var (
	ip      string
	thread  int
	timeout float64
)

func worker(i string, ports, results chan int) {
	for p := range ports {

		address := fmt.Sprintf("%s:%d", i, p)

		//fmt.Println(address)
		lock.RLock()
		count++
		rundata = p
		lock.RUnlock()

		//coon, err := net.Dial("tcp", address)
		coon, err := net.DialTimeout("tcp", address, time.Duration(timeout*1000)*time.Millisecond)
		if err != nil {
			results <- 0
			continue
		}
		defer coon.Close()

		// 发送数据
		msg := "Hello, Server!"
		_, err = coon.Write([]byte(msg))
		if err != nil {
			fmt.Println("\033[31m", address, "开放 \033[0m", "发送数据失败", "\033[K")
			results <- p
			continue
		}

		// 设置读取响应超时时间
		coon.SetReadDeadline(time.Now().Add(time.Duration(timeout*1000) * time.Millisecond))
		// 获取响应
		buf := make([]byte, 1024)
		n, err := coon.Read(buf)
		if err != nil {
			fmt.Println("\033[31m", address, "开放 \033[0m", "获取banner失败", err, "\033[K")
			results <- p
			continue
		}

		banner := strings.ReplaceAll(string(buf[:n]), "\n", "\\n")
		banner = strings.ReplaceAll(banner, "\r", "")
		fmt.Println("\033[31m", address, "开放 \033[0m", banner, "\033[K")
		results <- p

	}
}

func Init() {
	flag.StringVar(&ip, "ip", "", "扫描IP地址")
	flag.IntVar(&thread, "thread", 200, "扫描线程数")
	flag.Float64Var(&timeout, "timeout", 1, "设置端口连接超时时间,单位秒")
	flag.Parse()
	if ip == "" {
		fmt.Println("The parameter is empty. Here is the usage:")
		flag.PrintDefaults()
		os.Exit(1)
	}
}

func main() {

	Init()
	ports := make(chan int, thread)
	results := make(chan int)

	totleNum := 65535
	bar_width := 60

	var openports []string

	// Ticker 包含一个通道字段C，每隔时间段 d 就向该通道发送当时系统时间。
	// 它会调整时间间隔或者丢弃 tick 信息以适应反应慢的接收者。
	// 如果d <= 0会触发panic。关闭该 Ticker 可以释放相关资源。
	ticker1 := time.NewTicker(1000 * time.Millisecond)
	// 一定要调用Stop()，回收资源
	defer ticker1.Stop()

	for i := 0; i < cap(ports); i++ {
		go worker(ip, ports, results)
	}

	go func() {
		for i := 1; i <= totleNum; i++ {
			ports <- i
		}
	}()

	// 使用定时器 显示进度条
	go func(t *time.Ticker) {
		for {
			// 每5秒中从chan t.C 中读取一次
			<-t.C
			//fmt.Println("Ticker:", time.Now().Format("2006-01-02 15:04:05"))
			bar := int(bar_width * count / totleNum)
			percentage := int((float32(count) / float32(totleNum)) * 100)
			//print(f'正在扫描{queue_data}#\t[{"█"*bar}{" "*(bar_width-bar)}] {percentage}％', end='\r', flush=True)
			fmt.Printf("正在扫描端口%d #\t [%v%v] %d％\r", rundata, strings.Repeat("█", bar), strings.Repeat(" ", bar_width-bar), percentage)

		}
	}(ticker1)

	for i := 1; i <= totleNum; i++ {
		port := <-results
		if port != 0 {
			openports = append(openports, strconv.Itoa(port))
		}

	}
	close(ports)
	//close(results)
	////fmt.Println("开始排序")
	//sort.Ints(openports)

	fmt.Println("扫描完成", "\033[K")
	fmt.Println(strings.Join(openports, ","))
}

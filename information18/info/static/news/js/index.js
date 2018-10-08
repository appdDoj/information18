var currentCid = 1; // 当前分类 id
var cur_page = 1; // 当前页
var total_page = 1;  // 总页数
var data_querying = false;   // 是否正在向后台获取数据


$(function () {

    updateNewsData()
    // 首页分类切换
    $('.menu li').click(function () {
        var clickCid = $(this).attr('data-cid')
        $('.menu li').each(function () {
            $(this).removeClass('active')
        })
        $(this).addClass('active')

        if (clickCid != currentCid) {
            // 记录当前分类id
            currentCid = clickCid

            // 重置分页参数
            cur_page = 1
            total_page = 1
            updateNewsData()
        }
    })

    //页面滚动加载相关
    $(window).scroll(function () {

        // 浏览器窗口高度
        var showHeight = $(window).height();

        // 整个网页的高度
        var pageHeight = $(document).height();

        // 页面可以滚动的距离
        var canScrollHeight = pageHeight - showHeight;

        // 页面滚动了多少,这个是随着页面滚动实时变化的
        var nowScroll = $(document).scrollTop();

        if ((canScrollHeight - nowScroll) < 100) {
            // TODO 判断页数，去更新新闻数据

            // data_querying=false 表示没有人在请求数据，可以进入if判断去加载数据
            if(!data_querying){
                console.log("来了吗？")
                if(cur_page <= total_page){
                    // 将标志位该成True表示有人在加载数据，不需要再次发送请求
                    data_querying = true
                    // 加载下一页的数据
                    updateNewsData()
                }else{
                    // 页码超出了
                    data_querying = false
                }

            }

        }
    })
})

function updateNewsData() {
    // TODO 更新新闻数据
    // 组织请求数据
    var params = {
        "page": cur_page,
        "cid": currentCid,
        'per_page': 10
    }
    $.get("/news_list", params, function (resp) {
        if (resp) {

            // 将总页码赋值
            total_page = resp.data.total_page
            // 当本次请求数据完毕之后，再次将标志位改成false，下次才能继续拉下加载更多
            data_querying = false
            if(cur_page == 1){
                // 先清空原有数据
                $(".list_con").html('')
            }
            //当前页码加一
            cur_page += 1

            // 显示数据
            for (var i=0;i<resp.data.news_list.length;i++) {
                var news = resp.data.news_list[i]
                var content = '<li>'
                content += '<a href="#" class="news_pic fl"><img src="' + news.index_image_url + '?imageView2/1/w/170/h/170"></a>'
                content += '<a href="#" class="news_title fl">' + news.title + '</a>'
                content += '<a href="#" class="news_detail fl">' + news.digest + '</a>'
                content += '<div class="author_info fl">'
                content += '<div class="source fl">来源：' + news.source + '</div>'
                content += '<div class="time fl">' + news.create_time + '</div>'
                content += '</div>'
                content += '</li>'
                $(".list_con").append(content)
            }
        }
    })
}
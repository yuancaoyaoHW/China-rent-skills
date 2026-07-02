import unittest

import parse_fang_html


class FangHtmlParserTests(unittest.TestCase):
    def test_parse_block_uses_beike_community_search_url(self):
        block = """
        <p class="title" id="rentid_D09_01_02">
          <a href="/chuzu/3_432573337_1.htm" target="_blank"
             title="生活超便利不用爬楼梯玉香苑(三期) 精装修">
             生活超便利不用爬楼梯玉香苑(三期) 精装修
          </a>
        </p>
        <p class="font15 mt12 bold"> 整租<span class="splitline">|</span>2室1厅<span class="splitline">|</span>148㎡<span class="splitline">|</span>朝南 </p>
        <p class="gray6 mt12"><a href="//sh.zu.fang.com/house-a025/" target="_blank"><span>浦东</span></a>-张江-<a href="//sh.zu.fang.com/house-xm1210764912/" target="_blank"><span>玉兰香苑三期</span></a></p>
        <div><p class="mt12"><span class="note subInfor">距13号线张江路站约1020米。</span></p></div>
        <div class="moreInfo"><p class="mt5 alingC"><span class="price">3000</span>元/月</p></div>
        """

        rec = parse_fang_html._parse_block(block)

        self.assertEqual(
            rec["url"],
            "https://sh.zu.ke.com/zufang/rs%E7%8E%89%E5%85%B0%E9%A6%99%E8%8B%91%E4%B8%89%E6%9C%9F/",
        )


if __name__ == "__main__":
    unittest.main()

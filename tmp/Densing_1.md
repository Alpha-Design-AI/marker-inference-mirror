

{0}------------------------------------------------

## **Densing Law of LLMs**

Chaojun Xiao<sup>1</sup>, Jie Cai<sup>2</sup>, Weilin Zhao<sup>1</sup>, Guoyang Zeng<sup>2</sup>, Biyuan Lin<sup>2</sup>, Jie Zhou<sup>2</sup>, Zhi Zheng<sup>2</sup> Xu Han<sup>1</sup>, Zhiyuan Liu<sup>1</sup>, Maosong Sun<sup>1</sup>

> <sup>1</sup>Tsinghua University <sup>2</sup>ModelBest Inc. xiaocj20@mails.tsinghua.edu.cn {han-xu, liuzy, sms}@tsinghua.edu.cn

## **Highlights**

We introduce the concept of "capability density" to evaluate the training quality of large language models (LLMs) and describe the trend of LLMs that considers both effectiveness and efficiency.

(Relative) Capability Density. For a given LLM  $M$ , its capability density is defined as the ratio of its **effective parameter size** to its actual parameter size, where the effective parameter size is the minimum number of parameters required for the reference model to achieve performance equivalent to  $M$ .

We reveal an empirical law for the capability density of *open-source base LLMs* released since 2023.

**Densing Law.** The maximum capability density of LLMs exhibits an exponential growth trend over time.

 $ln(\rho_{max}) = At + B$ 

Here,  $\rho_{max}$  is the maximum capability density of LLMs at time t.

Figure 1 presents the capability density of popular LLMs, measured by their performance on 5 widely-used benchmarks. A trend is fitted between maximum capability density and release date, revealing that  $A \approx 0.007$  with  $R^2 \approx 0.93$ . This indicates the maximum capability density of **LLMs doubles approximately every 3.3 months**<sup>1</sup>. That means, around three months, it is possible to achieve performance comparable to current state-of-the-art LLMs using a model with half the parameter size.

![](_page_0_Figure_11.jpeg)

**Figure 1:** The estimated capability density of open-source base LLMs.

<sup>&</sup>lt;sup>1</sup>The capability density growth rate is affected by specific evaluation benchmarks and reference models.
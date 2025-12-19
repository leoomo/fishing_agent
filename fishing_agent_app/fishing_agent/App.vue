<template>
  <view class="content">
    <image class="logo" src="/static/logo.png" mode="aspectFit"></image>
    <view class="text-area">
      <text class="title">{{title}}</text>
    </view>
  </view>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      title: '路亚AI智能助手'
    }
  },
  onLaunch() {
    console.log('App Launch')
  },
  onShow() {
    console.log('App Show')
  },
  onHide() {
    console.log('App Hide')
  }
}
</script>

<style>
.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
}

.logo {
  height: 200rpx;
  width: 200rpx;
  margin-top: 200rpx;
  margin-left: auto;
  margin-right: auto;
  margin-bottom: 50rpx;
}

.text-area {
  display: flex;
  justify-content: center;
}

.title {
  font-size: 36rpx;
  color: #8f8f94;
}
</style>
